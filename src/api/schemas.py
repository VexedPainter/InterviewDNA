"""
src/api/schemas.py — Request and Response models for InterviewDNA FastAPI service.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.schemas.models import (
    CoachingAdvice,
    EvaluationResult,
    TurnRecord,
)

# -----------------------------------------------------------------------------
# Common / Error Responses
# -----------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Uniform error model returned across all endpoints on failure."""
    error: str = Field(..., description="High-level error category or name")
    detail: str = Field(..., description="Human-readable description or validation detail")


class HealthResponse(BaseModel):
    """Health check status model."""
    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(default="InterviewDNA API", description="Service name")
    version: str = Field(default="1.0.0", description="API version")
    models_loaded: bool = Field(default=True, description="Whether ML models & ChromaDB are preloaded")
    chroma_ready: bool = Field(default=True, description="Whether ChromaDB collections are accessible")
    llm_provider: str = Field(default="gemini", description="Active LLM provider")


# -----------------------------------------------------------------------------
# Company & DNA Schemas
# -----------------------------------------------------------------------------

class CompanyInfo(BaseModel):
    company: str
    roles: list[str]
    rounds: list[str]


class CompaniesResponse(BaseModel):
    """List of supported companies, available roles, and round progressions."""
    companies: list[str]
    roles: dict[str, list[str]]
    round_structures: dict[str, list[str]]
    company_details: list[CompanyInfo]


# -----------------------------------------------------------------------------
# Session Management Schemas
# -----------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    """Payload to initialize a new interview session."""
    nickname: str = Field(default="Student", min_length=1, max_length=50, description="Candidate nickname")
    company: str = Field(default="Zoho", description="Target company")
    role: str = Field(default="Software Developer", description="Target role")
    round_mode: str = Field(default="Technical", description="Starting round mode")
    difficulty_mode: int = Field(default=3, ge=1, le=5, description="Initial difficulty (1-5)")
    pressure_mode: bool = Field(default=False, description="Enable simulated timer pressure")


class CreateSessionResponse(BaseModel):
    """Response returned upon successful session creation."""
    session_id: str
    company: str
    role: str
    round_type: str
    difficulty_level: int
    first_question: TurnRecord | None = None
    message: str


class SendMessageRequest(BaseModel):
    """User input message sent during an interview session."""
    message: str = Field(..., min_length=1, max_length=4000, description="Candidate message or answer")


class AgentTrace(BaseModel):
    """Execution telemetry for agent dispatch and retrieval."""
    retrieved_count: int = Field(default=0, description="Number of archive records retrieved")
    fallback_level: str = Field(default="none", description="Retriever fallback tier applied")
    latency_ms: float = Field(default=0.0, description="Turn processing latency in milliseconds")


class SendMessageResponse(BaseModel):
    """Routed and evaluated turn response for an interview message."""
    routed_to: str
    confidence: float
    reply_type: str
    response_text: str
    question: TurnRecord | None = None
    evaluation: EvaluationResult | None = None
    coaching: CoachingAdvice | None = None
    followup: TurnRecord | None = None
    agent_trace: AgentTrace


class UserProgressResponse(BaseModel):
    """Historical session summary for a user nickname."""
    nickname: str
    total_sessions: int
    sessions: list[dict[str, Any]]
