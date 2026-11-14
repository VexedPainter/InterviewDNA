"""
tests/test_retriever.py — Unit and integration tests for InterviewRetriever.

Tests coverage:
1. Question retrieval with metadata filters (company, role, round_type, topic).
2. Question deduplication via exclude_ids.
3. Graceful fallback when role has insufficient questions.
4. Feedback retrieval with recency-weighted re-ranking.
5. Feedback fallback from company+role to company-only.
"""

from __future__ import annotations

import pytest

from src.rag.retriever import InterviewRetriever


@pytest.fixture(scope="module")
def retriever():
    """Module-level retriever fixture using persisted Chroma collections."""
    return InterviewRetriever()


def test_get_questions_company_filter(retriever: InterviewRetriever):
    """Test questions match requested company and role."""
    res = retriever.get_questions(
        company="Zoho",
        role="Software Developer",
        k=3,
    )
    assert len(res.items) > 0
    assert res.fallback_level in ("company_role", "company_only")
    for item in res.items:
        assert item.company == "Zoho"
        assert item.question != ""
        assert item.difficulty in [1, 2, 3, 4, 5]


def test_get_questions_topic_filter(retriever: InterviewRetriever):
    """Test questions match specific topic if present."""
    res = retriever.get_questions(
        company="Amazon",
        role="SDE-I",
        topic="DSA",
        k=3,
    )
    assert len(res.items) > 0
    # Every item returned should be DSA when available
    for item in res.items:
        assert item.topic == "DSA"


def test_get_questions_exclusion(retriever: InterviewRetriever):
    """Test that exclude_ids prevents already-asked questions from recurring."""
    initial_res = retriever.get_questions(company="Google", role="Software Engineer", k=2)
    assert len(initial_res.items) >= 2
    excluded = [item.record_id for item in initial_res.items]

    # Query again excluding the first batch
    subsequent_res = retriever.get_questions(
        company="Google",
        role="Software Engineer",
        exclude_ids=excluded,
        k=2,
    )
    returned_ids = [item.record_id for item in subsequent_res.items]
    for eid in excluded:
        assert eid not in returned_ids, f"Excluded ID {eid} was returned!"


def test_get_questions_fallback(retriever: InterviewRetriever):
    """Test fallback from non-existent role to company_only."""
    res = retriever.get_questions(
        company="Flipkart",
        role="NonExistentRole12345",
        k=4,
    )
    assert len(res.items) > 0
    assert res.fallback_level == "company_only"
    for item in res.items:
        assert item.company == "Flipkart"


def test_get_feedback_recency_reranking(retriever: InterviewRetriever):
    """Test that recency weighting formula correctly differentiates older vs newer records."""
    res = retriever.get_feedback(
        company="Amazon",
        role="SDE-I",
        query="dynamic programming and leadership principles with STAR format",
        k=5,
        base_weight=0.7,
        recency_weight=0.3,
    )
    assert len(res.items) > 0
    # Verify final_score is correctly computed and ordered descending
    for i in range(len(res.items) - 1):
        curr = res.items[i]
        nxt = res.items[i + 1]
        assert curr.final_score >= nxt.final_score

        # Check recency factor bounds
        assert 0.0 <= curr.recency_factor <= 1.0

        # Check formula consistency
        expected_score = round(curr.raw_similarity * (0.7 + 0.3 * curr.recency_factor), 4)
        assert abs(curr.final_score - expected_score) < 0.01


def test_get_feedback_fallback(retriever: InterviewRetriever):
    """Test feedback fallback when an unknown role is requested."""
    res = retriever.get_feedback(
        company="TCS",
        role="UnseenRole999",
        query="communication and basic coding",
        k=3,
    )
    assert len(res.items) > 0
    assert res.fallback_level == "company_only"
    for item in res.items:
        assert item.company == "TCS"
