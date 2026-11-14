"""
Tests for Phase 5: Four Agents & Orchestrator
---------------------------------------------
Tests InterviewerAgent, EvaluatorAgent, CoachAgent, ReportAgent,
and Orchestrator using FakeListChatModel and the real ChromaDB retriever.
"""

from __future__ import annotations

import json

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from src.agents.coach import CoachAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.interviewer import InterviewerAgent
from src.agents.report import ReportAgent
from src.memory.session_memory import SessionMemory, SQLiteSessionStore
from src.orchestrator import Orchestrator
from src.rag.retriever import InterviewRetriever
from src.schemas.models import (
    EvaluationResult,
    InterviewState,
    SessionReport,
)
from src.schemas.router import IntentType


@pytest.fixture
def retriever():
    return InterviewRetriever()


@pytest.fixture
def in_memory_store(tmp_path):
    test_db = str(tmp_path / "test_agents.db")
    return SQLiteSessionStore(db_path=test_db)


@pytest.fixture
def session_memory(in_memory_store):
    state = InterviewState(
        session_id="test_session_123",
        company="Zoho",
        role="Software Development Engineer",
        user_nickname="Tester",
        round_type="Technical",
        difficulty_level=3,
    )
    return SessionMemory(initial_state=state, sqlite_store=in_memory_store)


# =====================================================================
# InterviewerAgent Tests
# =====================================================================

def test_interviewer_picks_new_question_each_turn(retriever, session_memory, monkeypatch):
    # Mock LLM to avoid real API calls during styling
    fake_llm = FakeListChatModel(responses=["Could you explain this concept in detail?"])
    monkeypatch.setattr("src.agents.interviewer.get_llm", lambda **kwargs: fake_llm)

    agent = InterviewerAgent(retriever=retriever)

    # First turn
    turn1 = agent.run(session_memory)
    assert turn1.turn_number == 1
    assert turn1.question_id in session_memory.state.asked_ids
    assert len(session_memory.state.asked_ids) == 1

    # Fake answer and complete turn
    eval1 = EvaluationResult(correctness=8.0, depth=8.0, communication=8.0)
    session_memory.complete_active_turn(eval1)

    # Second turn
    turn2 = agent.run(session_memory)
    assert turn2.turn_number == 2
    assert turn2.question_id in session_memory.state.asked_ids
    assert len(session_memory.state.asked_ids) == 2
    assert turn1.question_id != turn2.question_id


def test_interviewer_difficulty_adapts_up(retriever, session_memory, monkeypatch):
    fake_llm = FakeListChatModel(responses=["Styled Q1", "Styled Q2", "Styled Q3"])
    monkeypatch.setattr("src.agents.interviewer.get_llm", lambda **kwargs: fake_llm)

    agent = InterviewerAgent(retriever=retriever)
    session_memory.state.difficulty_level = 3

    # Turn 1: score 8
    agent.run(session_memory)
    session_memory.complete_active_turn(EvaluationResult(correctness=8.0, depth=8.0, communication=8.0))

    # Turn 2: score 9
    agent.run(session_memory)
    session_memory.complete_active_turn(EvaluationResult(correctness=9.0, depth=9.0, communication=9.0))

    # Turn 3: difficulty should now adapt from 3 to 4
    agent.run(session_memory)
    assert session_memory.state.difficulty_level == 4


def test_interviewer_difficulty_adapts_down(retriever, session_memory, monkeypatch):
    fake_llm = FakeListChatModel(responses=["Styled Q1", "Styled Q2", "Styled Q3"])
    monkeypatch.setattr("src.agents.interviewer.get_llm", lambda **kwargs: fake_llm)

    agent = InterviewerAgent(retriever=retriever)
    session_memory.state.difficulty_level = 3

    # Turn 1: score 3
    agent.run(session_memory)
    session_memory.complete_active_turn(EvaluationResult(correctness=3.0, depth=3.0, communication=3.0))

    # Turn 2: score 4
    agent.run(session_memory)
    session_memory.complete_active_turn(EvaluationResult(correctness=4.0, depth=4.0, communication=4.0))

    # Turn 3: difficulty should adapt down from 3 to 2
    agent.run(session_memory)
    assert session_memory.state.difficulty_level == 2


def test_interviewer_followup_generation(retriever, session_memory, monkeypatch):
    fake_llm = FakeListChatModel(responses=["Can you specifically address the space complexity?"])
    monkeypatch.setattr("src.agents.interviewer.get_llm", lambda **kwargs: fake_llm)

    agent = InterviewerAgent(retriever=retriever)
    agent.run(session_memory)

    eval_result = EvaluationResult(
        correctness=6.0,
        depth=5.0,
        communication=7.0,
        missed_points=["space complexity analysis"],
        needs_followup=True,
        followup_reason="Missed space complexity",
    )
    session_memory.complete_active_turn(eval_result)

    followup_turn = agent.generate_followup(session_memory, eval_result)
    assert followup_turn.is_followup is True
    assert "space complexity" in followup_turn.question.lower()


# =====================================================================
# EvaluatorAgent Tests
# =====================================================================

def test_evaluator_evaluates_answer(session_memory, monkeypatch):
    eval_json = json.dumps({
        "correctness": 8.0,
        "depth": 7.5,
        "communication": 9.0,
        "overall": 8.1,
        "matched_points": ["explained hash table collision resolution using chaining"],
        "missed_points": ["didn't discuss open addressing vs chaining trade-offs"],
        "red_flags": [],
        "needs_followup": False,
        "followup_reason": None,
    })
    fake_llm = FakeListChatModel(responses=[eval_json])
    monkeypatch.setattr("src.agents.evaluator.get_llm", lambda **kwargs: fake_llm)

    agent = EvaluatorAgent(self_consistency=False)

    turn = session_memory.start_new_turn(
        question="How do hash tables resolve collisions?",
        expected_points="chaining|open addressing|time complexity",
        question_id="Q_HASH",
        topic="DSA",
        round_type="Technical",
    )

    result = agent.run(
        candidate_answer="They use chaining with linked lists or open addressing with probing.",
        turn=turn,
        memory=session_memory,
    )

    assert result.correctness == 8.0
    assert result.overall == 8.1
    assert "chaining" in result.matched_points[0]
    assert session_memory.has_pending_question is False


def test_evaluator_star_detection_behavioral(session_memory, monkeypatch):
    eval_json = json.dumps({
        "correctness": 8.0,
        "depth": 8.0,
        "communication": 8.0,
        "overall": 8.0,
        "matched_points": ["Clear STAR structure: Situation and Task clearly established"],
        "missed_points": [],
        "red_flags": [],
        "needs_followup": False,
        "followup_reason": None,
    })
    fake_llm = FakeListChatModel(responses=[eval_json])
    monkeypatch.setattr("src.agents.evaluator.get_llm", lambda **kwargs: fake_llm)

    agent = EvaluatorAgent(self_consistency=False)

    turn = session_memory.start_new_turn(
        question="Tell me about a time you handled a conflict in your team.",
        expected_points="situation|action taken|resolution",
        question_id="Q_STAR",
        topic="Behavioral",
        round_type="HR",
    )

    result = agent.run(
        candidate_answer="In my final year project, our team disagreed on database choice...",
        turn=turn,
        memory=session_memory,
    )

    assert any("STAR" in p for p in result.matched_points)


def test_evaluator_self_consistency(session_memory, monkeypatch):
    # 3 responses with different scores: median of correctness (7, 8, 9) = 8
    res1 = json.dumps({"correctness": 7.0, "depth": 7.0, "communication": 7.0, "overall": 7.0, "matched_points": [], "missed_points": [], "red_flags": [], "needs_followup": False, "followup_reason": None})
    res2 = json.dumps({"correctness": 8.0, "depth": 8.0, "communication": 8.0, "overall": 8.0, "matched_points": [], "missed_points": [], "red_flags": [], "needs_followup": False, "followup_reason": None})
    res3 = json.dumps({"correctness": 9.0, "depth": 9.0, "communication": 9.0, "overall": 9.0, "matched_points": [], "missed_points": [], "red_flags": [], "needs_followup": False, "followup_reason": None})

    fake_llm = FakeListChatModel(responses=[res1, res2, res3])
    monkeypatch.setattr("src.agents.evaluator.get_llm", lambda **kwargs: fake_llm)

    agent = EvaluatorAgent(self_consistency=True)
    turn = session_memory.start_new_turn(
        question="Explain indexing.",
        expected_points="B-trees|lookup time",
        question_id="Q_IDX",
        topic="DBMS",
        round_type="Technical",
    )

    result = agent.run(
        candidate_answer="Indexing speeds up queries using B-Trees.",
        turn=turn,
        memory=session_memory,
    )

    assert result.correctness == 8.0
    assert result.overall == 8.0


# =====================================================================
# CoachAgent Tests
# =====================================================================

def test_coach_cites_evidence_ids(retriever, session_memory, monkeypatch):
    coach = CoachAgent(retriever=retriever)
    query = "How do I crack the Zoho technical round?"
    fb_res = retriever.get_feedback(company="Zoho", role="Software Development Engineer", query=query, k=5)
    valid_ids = [r.record_id for r in fb_res.items]
    valid_id_1 = valid_ids[0] if valid_ids else "REC_001"
    valid_year_1 = fb_res.items[0].year if fb_res.items else 2023

    advice_json = json.dumps({
        "summary": "Focus on writing clean syntax and time complexity analysis.",
        "tips": [
            {
                "text": "Write code on paper or whiteboards before typing, as Zoho penalises syntax errors.",
                "evidence_ids": [valid_id_1],
                "evidence_year": [valid_year_1],
            }
        ],
        "no_evidence_notice": None,
    })
    fake_llm = FakeListChatModel(responses=[advice_json])
    monkeypatch.setattr("src.agents.coach.get_llm", lambda **kwargs: fake_llm)

    advice = coach.run(session_memory, query=query)

    assert advice.summary != ""
    assert len(advice.tips) >= 1
    assert valid_id_1 in advice.tips[0].evidence_ids


def test_coach_handles_empty_evidence(session_memory, monkeypatch):
    # Mock retriever to return 0 results
    class EmptyRetriever:
        def get_feedback(self, *args, **kwargs):
            from src.schemas.rag import RetrievalResponse
            return RetrievalResponse(query="test", items=[], fallback_level="unfiltered")

    advice_json = json.dumps({
        "summary": "General advice for software roles.",
        "tips": [{"text": "Practice data structures.", "evidence_ids": [], "evidence_year": []}],
        "no_evidence_notice": "No historical feedback records were found.",
    })
    fake_llm = FakeListChatModel(responses=[advice_json])
    monkeypatch.setattr("src.agents.coach.get_llm", lambda **kwargs: fake_llm)

    coach = CoachAgent(retriever=EmptyRetriever())
    advice = coach.run(session_memory, query="Tips for unknown company")

    assert advice.no_evidence_notice is not None
    assert "No historical feedback" in advice.no_evidence_notice


# =====================================================================
# ReportAgent Tests
# =====================================================================

def test_report_agent_compiles_and_exports(session_memory):
    # Populate history with 2 turns
    session_memory.start_new_turn(
        question="Q1", expected_points="p1", question_id="Q1", topic="DSA", round_type="Technical"
    )
    session_memory.complete_active_turn(
        EvaluationResult(correctness=8.0, depth=7.0, communication=9.0, matched_points=["Arrays"], missed_points=["Trees"])
    )

    session_memory.start_new_turn(
        question="Q2", expected_points="p2", question_id="Q2", topic="DBMS", round_type="Technical"
    )
    session_memory.complete_active_turn(
        EvaluationResult(correctness=6.0, depth=6.0, communication=7.0, matched_points=["Indexes"], missed_points=["ACID"])
    )

    report_agent = ReportAgent()
    report = report_agent.run(session_memory)

    assert isinstance(report, SessionReport)
    assert len(report.turn_scores) == 2
    assert report.averages["overall"] > 0
    assert report.verdict in ["Selected Ready", "Borderline", "Needs Practice"]
    assert len(report.improvement_plan) > 0

    # Verify Markdown and PDF exports exist on disk
    from src.agents.report import REPORTS_DIR
    md_file = REPORTS_DIR / f"{session_memory.state.session_id}.md"
    pdf_file = REPORTS_DIR / f"{session_memory.state.session_id}.pdf"

    assert md_file.exists()
    assert pdf_file.exists()
    assert md_file.stat().st_size > 0
    assert pdf_file.stat().st_size > 0


# =====================================================================
# Orchestrator Integration Tests
# =====================================================================

def test_orchestrator_routes_and_dispatches(retriever, in_memory_store, monkeypatch):
    sessions = {}
    orchestrator = Orchestrator(retriever=retriever, sqlite_store=in_memory_store)

    # 1. PRACTICE intent
    fake_interviewer_llm = FakeListChatModel(responses=[
        "Can you implement binary search?",
        "Next question: Explain OOP principles.",
        "Another technical question.",
    ])
    monkeypatch.setattr("src.agents.interviewer.get_llm", lambda **kwargs: fake_interviewer_llm)

    res_practice = orchestrator.handle_message(
        session_id="orch_test_1",
        user_message="I want to start the interview",
        sessions_dict=sessions,
        company="Zoho",
        role="Software Development Engineer",
    )
    assert res_practice["routing"].intent == IntentType.PRACTICE
    assert "binary search" in res_practice["response"].lower()
    assert sessions["orch_test_1"].has_pending_question is True

    # 2. EVALUATE intent (answering the question)
    eval_json = json.dumps({
        "correctness": 9.0,
        "depth": 8.0,
        "communication": 9.0,
        "overall": 8.65,
        "matched_points": ["Binary search iterative approach"],
        "missed_points": [],
        "red_flags": [],
        "needs_followup": False,
        "followup_reason": None,
    })
    fake_eval_llm = FakeListChatModel(responses=[eval_json, "Next question: Explain OOP principles."])
    monkeypatch.setattr("src.agents.evaluator.get_llm", lambda **kwargs: fake_eval_llm)

    res_eval = orchestrator.handle_message(
        session_id="orch_test_1",
        user_message="Binary search compares target with middle element and halves search space O(log N).",
        sessions_dict=sessions,
    )
    assert res_eval["routing"].intent == IntentType.EVALUATE
    assert res_eval["evaluation"] is not None
    assert res_eval["evaluation"].overall == pytest.approx(8.7, abs=0.1)

    # 3. REPORT intent
    res_report = orchestrator.handle_message(
        session_id="orch_test_1",
        user_message="end interview and give me report",
        sessions_dict=sessions,
    )
    assert res_report["routing"].intent == IntentType.REPORT
    assert res_report["report"] is not None
    assert "InterviewDNA Session Complete" in res_report["response"]
