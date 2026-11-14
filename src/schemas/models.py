"""
src/schemas/models.py — Pydantic models for InterviewDNA state, evaluation, coaching, and reports.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class EvaluationResult(BaseModel):
    """Structured evaluation of a single candidate answer against rubric."""
    correctness: float = Field(ge=0.0, le=10.0, description="Factual correctness and accuracy (0-10)")
    depth: float = Field(ge=0.0, le=10.0, description="Technical depth, trade-offs, edge cases (0-10)")
    communication: float = Field(ge=0.0, le=10.0, description="Clarity, structure, terminology (0-10)")
    overall: float = Field(default=0.0, ge=0.0, le=10.0, description="Weighted composite score (0-10)")
    matched_points: list[str] = Field(default_factory=list, description="Expected points covered well")
    missed_points: list[str] = Field(default_factory=list, description="Expected points missed or weak")
    red_flags: list[str] = Field(default_factory=list, description="Critical conceptual errors or flaws")
    needs_followup: bool = Field(default=False, description="Whether adaptive follow-up is warranted")
    followup_reason: str | None = Field(default=None, description="Reason for follow-up probe")

    @model_validator(mode="before")
    @classmethod
    def compute_overall_if_omitted(cls, data: Any) -> Any:
        """Computes weighted overall score if omitted or set to None/0."""
        if isinstance(data, dict):
            overall_val = data.get("overall")
            if overall_val is None or overall_val == 0.0:
                c = float(data.get("correctness", 5.0))
                d = float(data.get("depth", 5.0))
                comm = float(data.get("communication", 5.0))
                data["overall"] = round(0.4 * c + 0.35 * d + 0.25 * comm, 1)
            else:
                data["overall"] = round(float(overall_val), 1)
        return data


class TurnRecord(BaseModel):
    """Details of a single interview turn (question + answer + evaluation)."""
    turn_number: int
    question_id: str | None = None
    question: str
    expected_points: list[str] = Field(default_factory=list)
    candidate_answer: str = ""
    is_followup: bool = False
    evaluation: EvaluationResult | None = None
    topic: str | None = None
    round_type: str | None = None

    @field_validator("expected_points", mode="before")
    @classmethod
    def parse_expected_points(cls, v):
        if isinstance(v, str):
            return [p.strip() for p in v.split("|") if p.strip()]
        return v or []


class InterviewState(BaseModel):
    """Full conversational and session state of an interview in progress."""
    session_id: str
    company: str
    role: str
    round_type: str = "Technical"
    difficulty_level: int = Field(default=3, ge=1, le=5)
    asked_ids: list[str] = Field(default_factory=list, description="Record IDs of questions already asked")
    turn_count: int = 0
    followup_count: int = 0
    max_turns: int = Field(default=5, ge=1, le=20)
    is_completed: bool = False
    history: list[TurnRecord] = Field(default_factory=list)


class CoachingTip(BaseModel):
    """Specific coaching tip with required grounding citations."""
    text: str = Field(description="Actionable advice grounded in historical pattern")
    evidence_ids: list[str] = Field(default_factory=list, description="Citations to archive record_ids")
    evidence_year: int | list[int] | None = Field(default=None, description="Year of cited historical precedent")

    @field_validator("evidence_year", mode="before")
    @classmethod
    def parse_evidence_year(cls, v):
        if isinstance(v, list):
            return v[0] if v else None
        return v


class CoachingAdvice(BaseModel):
    """Personalised coaching grounded in company-specific historical feedback."""
    summary: str = Field(description="High-level feedback overview")
    tips: list[CoachingTip] = Field(default_factory=list, description="List of grounded coaching tips")
    no_evidence_notice: str | None = Field(
        default=None,
        description="Explicit disclosure if no direct company precedent was retrieved"
    )


class TurnScore(BaseModel):
    """Score summary for a single interview turn in the final report."""
    turn_number: int
    question: str = ""
    question_id: str | None = None
    topic: str | None = None
    round_type: str | None = None
    correctness: float
    depth: float
    communication: float
    overall: float
    is_followup: bool = False


class SessionReport(BaseModel):
    """Comprehensive post-interview session report and improvement roadmap."""
    session_id: str
    company: str
    role: str
    scores_per_turn: list[TurnScore] = Field(default_factory=list)
    averages: dict[str, float] = Field(default_factory=dict)
    trend: str = "flat"
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    improvement_plan: list[str] = Field(default_factory=list)
    benchmark_comparison: dict[str, Any] = Field(default_factory=dict)
    final_verdict: str = Field(default="Needs Practice", description="Selected Ready | Borderline | Needs Practice")

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "turn_scores" in data and "scores_per_turn" not in data:
                data["scores_per_turn"] = data["turn_scores"]
            if "top_strengths" in data and "strengths" not in data:
                data["strengths"] = data["top_strengths"]
            if "top_gaps" in data and "gaps" not in data:
                data["gaps"] = data["top_gaps"]
            if "verdict" in data and "final_verdict" not in data:
                data["final_verdict"] = data["verdict"]
        return data

    @property
    def turn_scores(self) -> list[TurnScore]:
        return self.scores_per_turn

    @property
    def top_strengths(self) -> list[str]:
        return self.strengths

    @property
    def top_gaps(self) -> list[str]:
        return self.gaps

    @property
    def verdict(self) -> str:
        return self.final_verdict
