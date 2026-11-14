"""
src/schemas/rag.py — Data schemas for RAG retrieval and Company DNA.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QuestionResult(BaseModel):
    """A retrieved historical interview question with metadata."""
    record_id: str
    question: str
    expected_points: list[str] = Field(default_factory=list)
    company: str
    role: str
    round_type: str
    topic: str
    difficulty: int
    year: int
    similarity: float = 0.0


class FeedbackResult(BaseModel):
    """A retrieved historical interview feedback record with re-ranked scores."""
    record_id: str
    feedback_text: str
    candidate_answer_summary: str
    company: str
    role: str
    round_type: str
    topic: str
    year: int
    feedback_tags: list[str] = Field(default_factory=list)
    score_given: float
    outcome: str
    raw_similarity: float = 0.0
    recency_factor: float = 0.0
    final_score: float = 0.0


class RetrievalResponse(BaseModel):
    """Encapsulates retrieval results and the fallback level used."""
    items: list[Any] = Field(default_factory=list)
    fallback_level: str = "company_role"  # "company_role" | "company_only" | "unfiltered"
    query: str | None = None
    total_found: int = 0

    @property
    def results(self) -> list[Any]:
        """Alias for items for backward compatibility."""
        return self.items


class CompanyDNAProfile(BaseModel):
    """Statistical and behavioural DNA profile for a company/role."""
    company: str
    role: str | None = None
    total_records: int
    selection_rate: float
    avg_difficulty: float
    difficulty_trend_by_year: dict[int, float]
    topic_distribution: dict[str, float]
    round_distribution: dict[str, float]
    top_rejection_tags: list[dict[str, Any]]
    top_positive_tags: list[dict[str, Any]]
    interviewer_style_summary: str
    generated_at: str
