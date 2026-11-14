"""
Coach Agent
-----------
Retrieves historical feedback records for the company/role/topic and
generates grounded, evidence-cited coaching advice.
"""

from __future__ import annotations

import logging
from collections import Counter

from src.llm.prompts import COACH_PROMPT, parse_structured_output
from src.llm.provider import get_llm
from src.memory.session_memory import SessionMemory
from src.rag.retriever import InterviewRetriever
from src.schemas.models import CoachingAdvice, CoachingTip

logger = logging.getLogger(__name__)

NO_EVIDENCE_MSG = (
    "No historical feedback records were found for this company/role. "
    "The advice below is general best-practice guidance, not grounded in "
    "real interview data for this specific context."
)


class CoachAgent:
    """Produces evidence-grounded coaching advice."""

    def __init__(self, retriever: InterviewRetriever) -> None:
        self.retriever = retriever

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, memory: SessionMemory, query: str) -> CoachingAdvice:
        """
        Generate coaching advice for the student.
        Every tip cites evidence_ids from retrieved feedback records.
        """
        state = memory.state

        # Build a focused retrieval query
        missed_points_str = self._get_missed_points(memory)
        topic = self._get_last_topic(memory)
        retrieval_query = f"{query} {missed_points_str} {topic}".strip()

        # Retrieve feedback evidence
        feedback_response = self.retriever.get_feedback(
            company=state.company,
            role=state.role,
            query=retrieval_query,
            k=5,
        )

        no_evidence_notice = None
        evidence_records: list[dict] = []

        if not feedback_response.results:
            no_evidence_notice = NO_EVIDENCE_MSG
            logger.info("CoachAgent: no evidence found; returning general advice.")
        else:
            for fb in feedback_response.items:
                tags = "|".join(fb.feedback_tags) if isinstance(fb.feedback_tags, list) else str(fb.feedback_tags)
                evidence_records.append(
                    {
                        "record_id": fb.record_id,
                        "year": fb.year,
                        "feedback_text": fb.feedback_text,
                        "feedback_tags": tags,
                        "outcome": fb.outcome,
                        "score_given": fb.score_given,
                    }
                )

        # Compute reward/penalise insights from tag frequencies
        reward_insight, penalise_insight = self._compute_tag_insights(feedback_response.items)

        # Format evidence for the prompt
        evidence_text = self._format_evidence(evidence_records)

        try:
            llm = get_llm(temperature=0.4)
            last_turn = state.history[-1] if state.history else None
            last_eval = last_turn.evaluation if last_turn else None

            variables = {
                "company": state.company,
                "role": state.role,
                "topic": topic or "General",
                "query": query,
                "retrieved_evidence": evidence_text,
                "question": last_turn.question if last_turn else query,
                "candidate_answer": (last_turn.candidate_answer if last_turn and last_turn.candidate_answer else "N/A"),
                "correctness": last_eval.correctness if last_eval else 0.0,
                "depth": last_eval.depth if last_eval else 0.0,
                "communication": last_eval.communication if last_eval else 0.0,
                "matched_points": (", ".join(last_eval.matched_points) if last_eval and last_eval.matched_points else "None"),
                "missed_points": (", ".join(last_eval.missed_points) if last_eval and last_eval.missed_points else "None"),
                "red_flags": (", ".join(last_eval.red_flags) if last_eval and last_eval.red_flags else "None"),
                "reward_insight": reward_insight,
                "penalise_insight": penalise_insight,
                "no_evidence_notice": no_evidence_notice or "",
            }

            advice = parse_structured_output(llm, COACH_PROMPT, variables, CoachingAdvice)
        except Exception as exc:
            logger.warning("CoachAgent LLM unavailable (%s); synthesizing grounded advice directly from evidence.", exc)
            fallback_tips = []
            if evidence_records:
                for rec in evidence_records[:3]:
                    clean_fb = (rec.get("feedback") or "Candidate demonstrated domain competence.").strip()
                    if len(clean_fb) > 140:
                        clean_fb = clean_fb[:137] + "..."
                    fallback_tips.append(
                        CoachingTip(
                            text=f"Historical Archive Insight: {clean_fb}",
                            evidence_ids=[rec["record_id"]],
                            evidence_year=[int(rec["year"]) if str(rec.get("year", "")).isdigit() else 2023],
                        )
                    )
            if not fallback_tips:
                fallback_tips.append(
                    CoachingTip(
                        text="Review core placement fundamentals and practice structured problem solving.",
                        evidence_ids=[],
                        evidence_year=[],
                    )
                )
            advice = CoachingAdvice(
                summary=f"Grounded preparation guidance for {state.company} ({state.role}) based on {len(evidence_records)} archive records.",
                tips=fallback_tips,
                no_evidence_notice=no_evidence_notice if not evidence_records else None,
            )

        # Enforce grounding: strip tips that claim evidence IDs not in our records
        if evidence_records:
            valid_ids = {r["record_id"] for r in evidence_records}
            for tip in advice.tips:
                tip.evidence_ids = [eid for eid in tip.evidence_ids if eid in valid_ids]

        if no_evidence_notice:
            advice.no_evidence_notice = no_evidence_notice

        return advice

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_missed_points(self, memory: SessionMemory) -> str:
        history = memory.state.history
        if history:
            last = history[-1]
            if last.evaluation and last.evaluation.missed_points:
                return " ".join(last.evaluation.missed_points)
        return ""

    def _get_last_topic(self, memory: SessionMemory) -> str:
        history = memory.state.history
        if history and history[-1].topic:
            return history[-1].topic
        return ""

    def _compute_tag_insights(self, results: list) -> tuple[str, str]:
        """
        Compute top rewarded / penalised behaviours from feedback_tags.
        Selected candidates' tags → rewards; Rejected candidates' tags → penalised.
        """
        rewarded: Counter = Counter()
        penalised: Counter = Counter()

        for fb in results:
            tags = fb.feedback_tags if isinstance(fb.feedback_tags, list) else [t.strip() for t in str(fb.feedback_tags).split("|") if t.strip()]
            outcome = getattr(fb, "outcome", "")
            if outcome == "Selected":
                rewarded.update(tags)
            elif outcome == "Rejected":
                penalised.update(tags)

        reward_str = (
            ", ".join(tag for tag, _ in rewarded.most_common(3))
            if rewarded
            else "strong fundamentals and clear communication"
        )
        penalise_str = (
            ", ".join(tag for tag, _ in penalised.most_common(3))
            if penalised
            else "lack of depth and vague answers"
        )
        return reward_str, penalise_str

    def _format_evidence(self, records: list[dict]) -> str:
        if not records:
            return "No historical feedback records available."
        lines = []
        for r in records:
            lines.append(
                f"[{r['record_id']} | {r['year']} | Outcome: {r['outcome']} | Score: {r['score_given']}]\n"
                f"Tags: {r['feedback_tags']}\n"
                f"Feedback: {r['feedback_text']}\n"
            )
        return "\n---\n".join(lines)
