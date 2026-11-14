"""
src/router/intent_router.py — State-aware hybrid Intent Router using LangChain Expression Language (LCEL).

Combines:
1. Fast-path regex / pattern matching for common signals.
2. Conversational state awareness (pending question -> EVALUATE).
3. LLM classifier chain fallback for nuanced queries.
4. RunnableBranch dispatcher returning rich routing metadata.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch, RunnableLambda
from pydantic import BaseModel, Field

from src.llm.provider import get_llm
from src.schemas.router import INTENT_TO_AGENT_MAP, IntentType, RoutingDecision

log = logging.getLogger(__name__)

# ==============================================================================
# Fast-Path Rule Definitions
# ==============================================================================

REPORT_PATTERNS = [
    r"\b(end|stop|finish|quit|terminate|exit)\b.*(interview|session)",
    r"\b(give|show|generate|compile|get)\b.*(report|summary|results|scorecard|feedback summary)",
    r"\b(wrap up|i('m| am) done|finished)\b",
]

COACH_PATTERNS = [
    r"\b(how (can|do) i improve|how to improve|what (should|can) i improve)\b",
    r"\b(give me|show me|want)\b.*(tips|coaching|advice|guidance|recommendations)",
    r"\b(what does|how does)\b.*(look for|care about|expect|evaluate)",
    r"\b(rejection reasons|why (do )?candidates fail|common mistakes|interview dna)\b",
    r"\bwhy (do )?(people|candidates|students) (fail|get rejected)\b",
    r"\bcoach(ing)? (me|mode|help)\b",
    r"\bcompany insights\b",
]

PRACTICE_PATTERNS = [
    r"\b(start|begin|commence|launch|want to)\b.*(interview|round|session|practic\w*)",
    r"\b(next|another|new|subsequent)\b.*(question|problem|prompt)",
    r"\b(i('m| am) ready|let('s| us) (start|begin|go)|ready for (the )?question)\b",
    r"\b(ask me|give me)\b.*(a|the|next)?\s*(question|problem)",
    r"\b(proceed|continue)\b",
]

SMALLTALK_PATTERNS = [
    r"^(hi|hello|hey|hola|namaste|greetings)\b",
    r"^(good (morning|afternoon|evening))\b",
    r"\b(who are you|what can you do|what is interviewdna|help me)\b",
]


def match_fast_path(message: str, has_pending_question: bool = False) -> RoutingDecision | None:
    """
    Evaluates rule-based fast paths.

    If a question is currently pending, answers to that question must NOT be intercepted
    by generic patterns unless the user explicitly asks to stop or requests coaching.
    """
    clean_msg = message.strip().lower()

    # 1. Report triggers always take highest priority
    for pat in REPORT_PATTERNS:
        if re.search(pat, clean_msg):
            return RoutingDecision(
                intent=IntentType.REPORT,
                confidence=1.0,
                reasoning=f"Matched report fast-path pattern: '{pat}'",
                routed_agent=INTENT_TO_AGENT_MAP[IntentType.REPORT],
                fast_path_used=True,
            )

    # 2. Coaching triggers take priority
    for pat in COACH_PATTERNS:
        if re.search(pat, clean_msg):
            return RoutingDecision(
                intent=IntentType.COACH,
                confidence=0.98,
                reasoning=f"Matched coaching fast-path pattern: '{pat}'",
                routed_agent=INTENT_TO_AGENT_MAP[IntentType.COACH],
                fast_path_used=True,
            )

    # 3. Practice triggers
    for pat in PRACTICE_PATTERNS:
        if re.search(pat, clean_msg):
            return RoutingDecision(
                intent=IntentType.PRACTICE,
                confidence=0.98,
                reasoning=f"Matched practice fast-path pattern: '{pat}'",
                routed_agent=INTENT_TO_AGENT_MAP[IntentType.PRACTICE],
                fast_path_used=True,
            )

    # 4. State-awareness: if a question is active and user didn't ask to quit/coach,
    # the user's message is an answer to be evaluated!
    if has_pending_question:
        # Check if it's not a pure greeting
        is_greeting = any(re.match(pat, clean_msg) for pat in SMALLTALK_PATTERNS)
        if not is_greeting and len(clean_msg) > 3:
            return RoutingDecision(
                intent=IntentType.EVALUATE,
                confidence=0.95,
                reasoning="Active pending question detected in session state; treating candidate response as answer to evaluate.",
                routed_agent=INTENT_TO_AGENT_MAP[IntentType.EVALUATE],
                fast_path_used=True,
            )

    # 5. Smalltalk / Greeting
    for pat in SMALLTALK_PATTERNS:
        if re.match(pat, clean_msg):
            return RoutingDecision(
                intent=IntentType.SMALLTALK_OR_UNCLEAR,
                confidence=0.95,
                reasoning=f"Matched smalltalk fast-path pattern: '{pat}'",
                routed_agent=INTENT_TO_AGENT_MAP[IntentType.SMALLTALK_OR_UNCLEAR],
                fast_path_used=True,
            )

    return None


# ==============================================================================
# LLM Classifier Fallback Chain (LCEL)
# ==============================================================================

ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are the Intent Classification Router for 'InterviewDNA', an agentic mock interview coach.\n"
        "Your task is to classify the user's intent into exactly ONE category:\n"
        "- PRACTICE: User wants to start or continue an interview, or asks for the next question.\n"
        "- EVALUATE: User is answering an interview question or providing technical explanation.\n"
        "- COACH: User is asking for feedback, tips, company insights, or how to improve.\n"
        "- REPORT: User wants to finish the session, see their scorecard, or get the summary report.\n"
        "- SMALLTALK_OR_UNCLEAR: Greetings, small talk, unrelated or ambiguous text.\n\n"
        "Session Context:\n"
        "Has Pending Question: {has_pending_question}\n\n"
        "Return ONLY a JSON object with keys: 'intent' (one of the 5 above), 'confidence' (float 0.0-1.0), and 'reasoning' (short explanation)."
    )),
    ("human", "User message to classify:\n\"{message}\"")
])


class LLMRoutingOutput(BaseModel):
    intent: IntentType
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    reasoning: str = ""


class IntentRouter:
    """
    Hybrid intent routing system combining fast paths, state awareness,
    and an LCEL LLM classifier fallback.
    """

    def __init__(self, llm: BaseChatModel | None = None):
        self.llm = llm

    def _get_llm(self) -> BaseChatModel:
        if self.llm is None:
            self.llm = get_llm(temperature=0.0)
        return self.llm

    def classify_intent(self, message: str, has_pending_question: bool = False) -> RoutingDecision:
        """
        Classifies user intent using fast paths first, falling back to LLM classifier.
        """
        # Step 1: Fast-path evaluation
        fast_decision = match_fast_path(message, has_pending_question=has_pending_question)
        if fast_decision is not None:
            return fast_decision

        # Step 2: LCEL LLM fallback
        try:
            llm = self._get_llm()
            chain = ROUTER_PROMPT | llm.with_structured_output(LLMRoutingOutput)
            output: LLMRoutingOutput = chain.invoke({
                "message": message,
                "has_pending_question": str(has_pending_question)
            })

            return RoutingDecision(
                intent=output.intent,
                confidence=output.confidence,
                reasoning=f"LLM classified: {output.reasoning}",
                routed_agent=INTENT_TO_AGENT_MAP.get(output.intent, "General Chat"),
                fast_path_used=False,
            )
        except Exception as e:
            log.warning("LLM router classification fallback triggered default due to: %s", e)
            # Safe heuristic fallback
            default_intent = IntentType.EVALUATE if has_pending_question else IntentType.SMALLTALK_OR_UNCLEAR
            return RoutingDecision(
                intent=default_intent,
                confidence=0.70,
                reasoning=f"Default heuristic fallback (error: {e})",
                routed_agent=INTENT_TO_AGENT_MAP.get(default_intent, "General Chat"),
                fast_path_used=False,
            )

    def build_dispatch_branch(
        self,
        practice_handler: Callable[[dict[str, Any]], Any],
        evaluate_handler: Callable[[dict[str, Any]], Any],
        coach_handler: Callable[[dict[str, Any]], Any],
        report_handler: Callable[[dict[str, Any]], Any],
        default_handler: Callable[[dict[str, Any]], Any] | None = None,
    ) -> RunnableBranch:
        """
        Constructs an LCEL RunnableBranch that dispatches incoming execution dicts
        to the appropriate agent handler.

        Input dict schema:
            { "message": str, "has_pending_question": bool, "state": Any, ... }

        Output dict schema:
            { "result": Any, "routing": RoutingDecision }
        """
        if default_handler is None:
            def default_handler(inputs: dict[str, Any]) -> dict[str, Any]:
                return {
                    "result": "Hello! I am InterviewDNA. You can say 'start interview' to practice, or ask for company tips and coaching.",
                    "routing": inputs.get("decision"),
                }

        def prepare_decision(inputs: dict[str, Any]) -> dict[str, Any]:
            msg = inputs.get("message", "")
            has_pending = inputs.get("has_pending_question", False)
            decision = self.classify_intent(msg, has_pending_question=has_pending)
            updated = dict(inputs)
            updated["decision"] = decision
            return updated

        def wrap_handler(handler: Callable[[dict[str, Any]], Any]) -> RunnableLambda:
            def _wrapped(inputs: dict[str, Any]) -> dict[str, Any]:
                res = handler(inputs)
                return {
                    "result": res,
                    "routing": inputs.get("decision"),
                }
            return RunnableLambda(_wrapped)

        branch = RunnableBranch(
            (lambda x: x["decision"].intent == IntentType.PRACTICE, wrap_handler(practice_handler)),
            (lambda x: x["decision"].intent == IntentType.EVALUATE, wrap_handler(evaluate_handler)),
            (lambda x: x["decision"].intent == IntentType.COACH, wrap_handler(coach_handler)),
            (lambda x: x["decision"].intent == IntentType.REPORT, wrap_handler(report_handler)),
            wrap_handler(default_handler),
        )

        return RunnableLambda(prepare_decision) | branch
