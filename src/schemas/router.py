"""
src/schemas/router.py — Pydantic models and Enums for Agentic Intent Routing.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class IntentType(StrEnum):
    """Supported user intent types for agentic dispatching."""
    PRACTICE = "PRACTICE"                    # start/continue interview, next question, ready
    EVALUATE = "EVALUATE"                    # message is an answer to the current question
    COACH = "COACH"                          # asks for tips, feedback, how to improve, company insights
    REPORT = "REPORT"                        # end session, summary report, finish interview
    SMALLTALK_OR_UNCLEAR = "SMALLTALK_OR_UNCLEAR"  # greeting, off-topic, unclear query


INTENT_TO_AGENT_MAP = {
    IntentType.PRACTICE: "Interviewer Agent",
    IntentType.EVALUATE: "Evaluator Agent",
    IntentType.COACH: "Coach Agent",
    IntentType.REPORT: "Report Agent",
    IntentType.SMALLTALK_OR_UNCLEAR: "General Chat",
}


class RoutingDecision(BaseModel):
    """The outcome of the intent routing pipeline."""
    intent: IntentType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: str = ""
    routed_agent: str = "General Chat"
    fast_path_used: bool = False

    @property
    def target_agent(self) -> str:
        return self.routed_agent
