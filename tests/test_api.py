"""
tests/test_api.py — Unit and integration tests for InterviewDNA REST API.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from src.api.main import app


@pytest.fixture
def client():
    """Provides a FastAPI TestClient."""
    return TestClient(app)


def test_health_endpoint(client):
    """GET /api/health should return 200 with service information."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "InterviewDNA API"
    assert data["version"] == "1.0.0"


def test_companies_endpoint(client):
    """GET /api/companies should list supported companies and roles."""
    response = client.get("/api/companies")
    assert response.status_code == 200
    data = response.json()
    assert "companies" in data
    assert "Zoho" in data["companies"]
    assert "Amazon" in data["companies"]
    assert "roles" in data
    assert "Zoho" in data["roles"]
    assert len(data["company_details"]) == len(data["companies"])


def test_company_dna_endpoint(client):
    """GET /api/companies/{company}/dna should return DNA profile."""
    response = client.get("/api/companies/Zoho/dna")
    assert response.status_code == 200
    data = response.json()
    assert data["company"].lower() == "zoho"
    assert "selection_rate" in data
    assert "avg_difficulty" in data
    assert "topic_distribution" in data
    assert "round_distribution" in data


def test_records_lookup_success_and_failure(client):
    """GET /api/records/{record_id} should return archive details or 404."""
    # Successful lookup
    resp = client.get("/api/records/AMA-2025-00832")
    assert resp.status_code == 200
    rec = resp.json()
    assert rec["record_id"] == "AMA-2025-00832"
    assert rec["company"] == "Amazon"
    assert "feedback_text" in rec

    # Missing lookup with uniform error response
    resp_404 = client.get("/api/records/NONEXISTENT-9999")
    assert resp_404.status_code == 404
    err = resp_404.json()
    assert "error" in err
    assert "detail" in err
    assert err["error"] == "Not Found"


def test_session_lifecycle(client, monkeypatch):
    """Tests creating a session, sending an answer, streaming, and ending the session."""
    # 1. Create Session
    fake_interviewer_llm = FakeListChatModel(responses=[
        "Here is a question on Arrays: How do you reverse an array in-place?"
    ])
    monkeypatch.setattr("src.agents.interviewer.get_llm", lambda **kw: fake_interviewer_llm)

    payload = {
        "nickname": "TesterAlex",
        "company": "Zoho",
        "role": "Software Developer",
        "round_mode": "Technical",
        "difficulty_mode": 3,
        "pressure_mode": False,
    }
    create_resp = client.post("/api/sessions", json=payload)
    assert create_resp.status_code == 200
    session_data = create_resp.json()
    session_id = session_data["session_id"]
    assert session_id is not None
    assert session_data["company"] == "Zoho"
    assert session_data["first_question"] is not None

    # 2. Send Answer (EVALUATE intent)
    eval_json = json.dumps({
        "correctness": 8.5,
        "depth": 8.0,
        "communication": 9.0,
        "overall": 8.45,
        "matched_points": ["Two pointer approach", "Swap elements until pointers meet"],
        "missed_points": [],
        "red_flags": [],
        "needs_followup": False,
        "followup_reason": None,
    })
    fake_eval_llm = FakeListChatModel(responses=[eval_json, "Next question: Explain OOP principles."])
    monkeypatch.setattr("src.agents.evaluator.get_llm", lambda **kw: fake_eval_llm)

    msg_payload = {
        "message": "We can use two pointers at start and end and swap elements moving towards center in O(N)."
    }
    msg_resp = client.post(f"/api/sessions/{session_id}/message", json=msg_payload)
    assert msg_resp.status_code == 200
    msg_data = msg_resp.json()
    assert msg_data["routed_to"] == "Evaluator Agent"
    assert msg_data["reply_type"] == "EVALUATE"
    assert msg_data["evaluation"] is not None
    assert msg_data["evaluation"]["overall"] > 8.0
    assert "agent_trace" in msg_data
    assert msg_data["agent_trace"]["latency_ms"] >= 0.0

    # 3. Stream Endpoint (SSE)
    stream_resp = client.get(f"/api/sessions/{session_id}/stream", params={"message": "can you give me coaching advice?"})
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]
    stream_content = stream_resp.text
    assert "data: " in stream_content
    assert "token" in stream_content or "complete" in stream_content

    # 4. End Session
    end_resp = client.post(f"/api/sessions/{session_id}/end")
    assert end_resp.status_code == 200
    report_data = end_resp.json()
    assert report_data["session_id"] == session_id
    assert "verdict" in report_data or "final_verdict" in report_data
    assert "averages" in report_data

    # 5. Check Reports (Markdown & PDF)
    md_resp = client.get(f"/api/sessions/{session_id}/report.md")
    assert md_resp.status_code == 200
    assert "text/markdown" in md_resp.headers["content-type"]
    assert "InterviewDNA Session Report" in md_resp.text

    # 6. User Progress
    progress_resp = client.get("/api/users/TesterAlex/progress")
    assert progress_resp.status_code == 200
    p_data = progress_resp.json()
    assert p_data["nickname"] == "TesterAlex"
    assert p_data["total_sessions"] >= 1


def test_validation_and_error_handling(client):
    """Tests uniform error format on bad input and 404s."""
    # Missing session 404
    resp = client.post("/api/sessions/nonexistent_123/message", json={"message": "hello"})
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data
    assert "detail" in data
    assert "Session 'nonexistent_123' not found" in data["detail"]

    # Invalid empty message validation
    resp_empty = client.post("/api/sessions/any/message", json={"message": ""})
    assert resp_empty.status_code == 422
    err_data = resp_empty.json()
    assert err_data["error"] == "Validation Error"
    assert "detail" in err_data
