"""
Interviewer Agent
-----------------
Picks the next question via RAG, adapts difficulty, handles follow-ups,
and phrases the question using the company's interviewer style.
"""

from __future__ import annotations

import logging

from config import settings
from src.llm.prompts import FOLLOWUP_PROMPT, INTERVIEWER_PROMPT
from src.llm.provider import get_llm
from src.memory.session_memory import SessionMemory
from src.rag.company_dna import CompanyDNABuilder
from src.rag.retriever import InterviewRetriever
from src.schemas.models import InterviewState, TurnRecord

logger = logging.getLogger(__name__)

# Default round progression for companies not in DNA cache
_DEFAULT_ROUND_ORDER = ["Aptitude", "Technical", "Managerial", "HR"]

# Company-specific round orders (overridden by DNA profile when available)
_COMPANY_ROUND_OVERRIDES: dict[str, list[str]] = {
    "Zoho": ["Aptitude", "Technical", "Technical", "Technical", "HR"],
    "Amazon": ["Aptitude", "Technical", "Technical", "Managerial", "HR"],
    "Google": ["Technical", "Technical", "Technical", "Managerial", "HR"],
    "TCS": ["Aptitude", "Technical", "Managerial", "HR"],
    "Infosys": ["Aptitude", "Technical", "HR"],
    "Accenture": ["Aptitude", "Technical", "Managerial", "HR"],
    "Deloitte": ["Aptitude", "Technical", "Managerial", "HR"],
    "Flipkart": ["Aptitude", "Technical", "Technical", "Managerial", "HR"],
}

TURNS_PER_ROUND: int = getattr(settings, "turns_per_round", 3)


class InterviewerAgent:
    """Conducts the interview turn-by-turn with adaptive difficulty."""

    def __init__(
        self,
        retriever: InterviewRetriever,
        dna_builder: CompanyDNABuilder | None = None,
    ) -> None:
        self.retriever = retriever
        self.dna_builder = dna_builder or CompanyDNABuilder(retriever)
        self._dna_cache: dict[str, object] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, memory: SessionMemory, style_with_llm: bool = True) -> TurnRecord:
        """
        Pick the next question, optionally style it using company DNA, and register it
        in memory.  Returns the newly created TurnRecord.
        """
        state = memory.state
        self._maybe_advance_round(state)

        difficulty = self._compute_difficulty(state)
        dna = self._get_dna(state.company, state.role)
        style_summary = dna.interviewer_style_summary if dna else ""

        question_result = self._fetch_question(state, difficulty)

        # Style the question text using the company's interviewer persona if requested
        if style_with_llm and style_summary:
            styled_question = self._style_question(
                raw_question=question_result["question"],
                style_summary=style_summary,
                company=state.company,
                role=state.role,
                round_type=state.round_type,
                turn_number=len(state.history) + 1,
                total_turns=state.max_turns,
                topic=question_result.get("topic", "General"),
                difficulty=difficulty,
                expected_points=question_result.get("expected_points", ""),
            )
        else:
            styled_question = question_result["question"]

        turn = memory.start_new_turn(
            question=styled_question,
            expected_points=question_result.get("expected_points", ""),
            question_id=question_result["id"],
            topic=question_result.get("topic", ""),
            round_type=state.round_type,
        )
        logger.info(
            "InterviewerAgent: asked question %s (difficulty=%s, round=%s)",
            question_result["id"],
            difficulty,
            state.round_type,
        )
        return turn

    def generate_followup(self, memory: SessionMemory, evaluation) -> TurnRecord:
        """
        Generate a probing follow-up question for the current turn's missed points.
        Called only when needs_followup=True and followup_count < 1.
        """
        state = memory.state
        last_turn = state.history[-1] if state.history else None
        missed = []
        if last_turn and last_turn.evaluation:
            missed = last_turn.evaluation.missed_points

        exp_str = ""
        if last_turn and last_turn.expected_points:
            exp_str = "|".join(last_turn.expected_points) if isinstance(last_turn.expected_points, list) else str(last_turn.expected_points)

        followup_text = self._generate_followup_text(
            original_question=last_turn.question if last_turn else "",
            missed_points=missed,
            company=state.company,
            role=state.role,
            expected_points=exp_str,
            candidate_answer=last_turn.candidate_answer if last_turn else "",
        )

        turn = memory.start_new_turn(
            question=followup_text,
            expected_points=last_turn.expected_points if last_turn else "",
            question_id=last_turn.question_id + "_followup" if last_turn else "followup",
            topic=last_turn.topic if last_turn else "",
            round_type=state.round_type,
            is_followup=True,
        )
        logger.info("InterviewerAgent: generated follow-up for %s", last_turn.question_id if last_turn else "?")
        return turn

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_dna(self, company: str, role: str):
        key = f"{company}::{role}"
        if key not in self._dna_cache:
            try:
                self._dna_cache[key] = self.dna_builder.get_or_build(company, role)
            except Exception as exc:
                logger.warning("Could not load DNA for %s/%s: %s", company, role, exc)
                self._dna_cache[key] = None
        return self._dna_cache[key]

    def _get_round_order(self, company: str, dna) -> list[str]:
        if dna and dna.round_distribution:
            # Sort by count descending, return round names
            ordered = sorted(dna.round_distribution.items(), key=lambda kv: kv[1], reverse=True)
            return [r for r, _ in ordered]
        return _COMPANY_ROUND_OVERRIDES.get(company, _DEFAULT_ROUND_ORDER)

    def _maybe_advance_round(self, state: InterviewState) -> None:
        """Advance round after TURNS_PER_ROUND questions in the current round."""
        current_round_turns = sum(
            1 for t in state.history if t.round_type == state.round_type and not t.is_followup
        )
        if current_round_turns > 0 and current_round_turns % TURNS_PER_ROUND == 0:
            dna = self._get_dna(state.company, state.role)
            round_order = self._get_round_order(state.company, dna)
            try:
                idx = round_order.index(state.round_type)
                if idx + 1 < len(round_order):
                    next_round = round_order[idx + 1]
                    if next_round != state.round_type:
                        logger.info(
                            "Advancing round: %s -> %s", state.round_type, next_round
                        )
                        state.round_type = next_round
            except ValueError:
                pass  # round not in list, stay put

    def _compute_difficulty(self, state: InterviewState) -> int:
        """
        Raise difficulty by 1 after two consecutive scores >= 7;
        lower by 1 after two consecutive scores <= 4.  Clamp [1, 5].
        """
        d = state.difficulty_level
        completed = [t for t in state.history if t.evaluation is not None and not t.is_followup]
        if len(completed) >= 2:
            last_two = [t.evaluation.overall for t in completed[-2:]]
            if all(s >= 7.0 for s in last_two):
                d = min(5, d + 1)
            elif all(s <= 4.0 for s in last_two):
                d = max(1, d - 1)
        state.difficulty_level = d
        return d

    def _fetch_question(self, state: InterviewState, difficulty: int) -> dict:
        """Retrieve next question from RAG with fallback."""
        low = max(1, difficulty - 1)
        high = min(5, difficulty + 1)
        results = self.retriever.get_questions(
            company=state.company,
            role=state.role,
            round_type=state.round_type,
            difficulty_range=(low, high),
            exclude_ids=list(state.asked_ids),
            k=5,
        )
        if not results.results:
            # Widen: any difficulty, same round
            results = self.retriever.get_questions(
                company=state.company,
                role=state.role,
                round_type=state.round_type,
                exclude_ids=list(state.asked_ids),
                k=5,
            )
        if not results.results:
            # Widest fallback: any round
            results = self.retriever.get_questions(
                company=state.company,
                role=state.role,
                exclude_ids=list(state.asked_ids),
                k=5,
            )
        if not results.results:
            # Emergency: return a placeholder
            logger.warning("No questions found in RAG; using emergency placeholder.")
            return {
                "id": "placeholder_q",
                "question": f"Tell me about a challenging {state.role} problem you solved recently.",
                "expected_points": "problem description|approach|outcome|learnings",
                "topic": "Behavioral",
            }

        top = results.items[0]
        expected = "|".join(top.expected_points) if isinstance(top.expected_points, list) else str(top.expected_points)
        return {
            "id": top.record_id,
            "question": top.question,
            "expected_points": expected,
            "topic": top.topic,
        }

    def _style_question(
        self,
        raw_question: str,
        style_summary: str,
        company: str,
        role: str,
        round_type: str,
        turn_number: int = 1,
        total_turns: int = 5,
        topic: str = "General",
        difficulty: int = 3,
        expected_points: str = "",
    ) -> str:
        """Use LLM to rephrase the question in the company's interviewer style."""
        if not style_summary:
            return raw_question
        try:
            llm = get_llm(temperature=0.3)
            prompt_value = INTERVIEWER_PROMPT.format_messages(
                company=company,
                role=role,
                round_type=round_type,
                turn_number=turn_number,
                total_turns=total_turns,
                topic=topic,
                difficulty=difficulty,
                expected_points=expected_points,
                question=raw_question,
            )
            response = llm.invoke(prompt_value)
            styled = response.content.strip()
            # Safety: if LLM hallucinated something too different, fall back
            if len(styled) < 10:
                return raw_question
            return styled
        except Exception as exc:
            logger.warning("Style rephrasing failed (%s); using raw question.", exc)
            return raw_question

    def _generate_followup_text(
        self,
        original_question: str,
        missed_points: list[str],
        company: str,
        role: str,
        expected_points: str = "",
        candidate_answer: str = "",
    ) -> str:
        """Generate a probing follow-up question via LLM."""
        missed_str = "; ".join(missed_points) if missed_points else "clarify your answer"
        try:
            llm = get_llm(temperature=0.5)
            prompt_value = FOLLOWUP_PROMPT.format_messages(
                company=company,
                role=role,
                question=original_question,
                expected_points=expected_points or missed_str,
                followup_reason=f"Missed points: {missed_str}",
                candidate_answer=candidate_answer or "Incomplete coverage of expected concepts.",
            )
            response = llm.invoke(prompt_value)
            return response.content.strip()
        except Exception as exc:
            logger.warning("Follow-up generation failed (%s); using default.", exc)
            return f"Can you elaborate further on: {missed_str}?"
