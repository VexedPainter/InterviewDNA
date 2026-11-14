"""
Evaluator Agent
---------------
Scores a candidate answer on correctness, depth, and communication
against retrieved expected_points.  Optionally runs self-consistency
(3 evaluations, median scores).  Detects STAR structure for Behavioral
questions.
"""

from __future__ import annotations

import logging
import re
import statistics

from config import settings
from src.llm.prompts import EVALUATOR_PROMPT, parse_structured_output
from src.llm.provider import get_llm
from src.memory.session_memory import SessionMemory
from src.schemas.models import EvaluationResult, TurnRecord

logger = logging.getLogger(__name__)

SELF_CONSISTENCY_RUNS: int = 3
MAX_ANSWER_LENGTH: int = 3000


class EvaluatorAgent:
    """Scores candidate answers and updates session memory."""

    def __init__(self, self_consistency: bool | None = None) -> None:
        self.self_consistency = (
            self_consistency
            if self_consistency is not None
            else getattr(settings, "self_consistency_enabled", False)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        candidate_answer: str,
        turn: TurnRecord,
        memory: SessionMemory | None = None,
    ) -> EvaluationResult:
        """
        Evaluate the candidate's answer for the given turn.
        Enforces input length bounds and safety guardrails.
        """
        raw_ans = (candidate_answer or "").strip()

        def _safe_commit(ev_result: EvaluationResult) -> None:
            if memory is not None:
                try:
                    if memory.active_turn is None:
                        memory.active_turn = turn
                    memory.complete_active_turn(ev_result)
                except Exception as mem_err:
                    logger.debug("Memory commit skipped: %s", mem_err)

        # Guardrail 1: Empty or extremely short input
        if len(raw_ans) < 5:
            ev = EvaluationResult(
                correctness=0.0,
                depth=0.0,
                communication=1.0,
                overall=0.25,
                matched_points=[],
                missed_points=["No substantive answer provided"],
                red_flags=["Empty or virtually empty submission"],
                needs_followup=True,
                followup_reason="Candidate provided no substantive answer.",
            )
            _safe_commit(ev)
            return ev

        # Guardrail 2: Input length limit
        if len(raw_ans) > MAX_ANSWER_LENGTH:
            logger.warning("Answer exceeded %d chars, truncating.", MAX_ANSWER_LENGTH)
            raw_ans = raw_ans[:MAX_ANSWER_LENGTH] + "... [truncated due to length limit]"

        # Guardrail 3: Blatant prompt injection without answering
        injection_patterns = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"give\s+me\s+10(\.0)?(\s*\/\s*10)?",
            r"output\s+10(\.0)?\s+for\s+all",
            r"disregard\s+(the\s+)?rubric",
        ]
        is_blatant_injection = any(re.search(pat, raw_ans, re.IGNORECASE) for pat in injection_patterns)
        expected_points_list = turn.expected_points if isinstance(turn.expected_points, list) else []
        has_substantive_answer = any(
            p.lower() in raw_ans.lower() for p in expected_points_list if len(p) > 3
        )

        if is_blatant_injection and not has_substantive_answer:
            ev = EvaluationResult(
                correctness=0.0,
                depth=0.0,
                communication=1.0,
                overall=0.25,
                matched_points=[],
                missed_points=["Did not address the technical or behavioral question"],
                red_flags=["Attempted prompt injection/instruction override"],
                needs_followup=True,
                followup_reason="Candidate submitted prompt manipulation instead of an answer.",
            )
            _safe_commit(ev)
            return ev

        try:
            llm = get_llm(temperature=0.0)
            variables = self._build_prompt_vars(raw_ans, turn, memory)

            if self.self_consistency:
                evaluation = self._evaluate_with_consistency(llm, variables, turn)
            else:
                evaluation = parse_structured_output(
                    llm, EVALUATOR_PROMPT, variables, EvaluationResult
                )
        except Exception as exc:
            logger.warning("LLM unavailable (%s); falling back to calibrated rubric heuristics.", exc)
            evaluation = self._heuristic_fallback_evaluation(raw_ans, turn)

        _safe_commit(evaluation)
        logger.info(
            "EvaluatorAgent: turn=%s overall=%.1f needs_followup=%s",
            turn.question_id,
            evaluation.overall,
            evaluation.needs_followup,
        )
        return evaluation

    def _heuristic_fallback_evaluation(self, candidate_answer: str, turn: TurnRecord) -> EvaluationResult:
        """Calibrated fallback evaluation when LLM provider is unavailable."""
        expected = turn.expected_points if isinstance(turn.expected_points, list) else [
            p.strip() for p in str(turn.expected_points or "").split("|") if p.strip()
        ]
        ans_lower = candidate_answer.lower()
        matched = []
        missed = []

        for p in expected:
            # Check key terms
            keywords = [w for w in re.findall(r"\w+", p.lower()) if len(w) > 3]
            if keywords and any(k in ans_lower for k in keywords) or not keywords and p.lower() in ans_lower:
                matched.append(p)
            else:
                missed.append(p)

        coverage = len(matched) / max(len(expected), 1) if expected else 0.5
        correctness = min(10.0, max(1.0, round(coverage * 8.5 + (1.2 if coverage > 0.5 else 0.0), 1)))

        has_complexity = bool(re.search(r"o\([n1klog\s\^]+\)", ans_lower) or "complexity" in ans_lower or "trade-off" in ans_lower)
        word_count = len(ans_lower.split())
        depth = min(10.0, max(1.0, round(
            (correctness * 0.7) + (2.0 if has_complexity else 0.0) + (1.0 if word_count > 25 else 0.0), 1
        )))

        is_behavioral = (turn.topic or "").lower() == "behavioral"
        star_found = any(k in ans_lower for k in ["situation", "task", "action", "result"]) if is_behavioral else False
        comm = min(10.0, max(2.0, round(
            (6.5 if word_count > 15 else 3.5) + (2.0 if star_found else 0.5), 1
        )))

        overall = round(0.4 * correctness + 0.35 * depth + 0.25 * comm, 1)

        red_flags = []
        if correctness <= 3.0:
            red_flags.append("Superficial answer missing core technical concepts")
        if is_behavioral and not star_found:
            red_flags.append("Missing STAR structure for behavioral question")

        return EvaluationResult(
            correctness=correctness,
            depth=depth,
            communication=comm,
            overall=overall,
            matched_points=matched if matched else ["Basic response attempted"],
            missed_points=missed,
            red_flags=red_flags,
            needs_followup=(overall < 6.0 or len(missed) > 1),
            followup_reason=f"Missed: {', '.join(missed[:2])}" if missed else None,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_prompt_vars(
        self, candidate_answer: str, turn: TurnRecord, memory: SessionMemory | None = None
    ) -> dict:
        is_behavioral = (turn.topic or "").lower() == "behavioral"
        star_instruction = (
            "Also detect whether the candidate used the STAR method "
            "(Situation, Task, Action, Result).  If STAR is well-structured, "
            "note it in matched_points.  If STAR is absent or incomplete for "
            "this Behavioral question, add a red_flag such as 'Missing STAR structure'."
            if is_behavioral
            else ""
        )
        expected_str = (
            ", ".join(turn.expected_points)
            if isinstance(turn.expected_points, list)
            else str(turn.expected_points or "")
        )
        comp = getattr(turn, "company", None) or (memory.state.company if memory else "")
        role = getattr(turn, "role", None) or (memory.state.role if memory else "")
        round_t = turn.round_type or (memory.state.round_type if memory else "")
        return {
            "company": comp,
            "role": role,
            "round_type": round_t,
            "topic": turn.topic or "",
            "question": turn.question,
            "expected_points": expected_str,
            "star_instruction": star_instruction,
            "candidate_answer": candidate_answer,
        }

    def _evaluate_with_consistency(self, llm, variables: dict, turn: TurnRecord) -> EvaluationResult:
        """Run evaluation SELF_CONSISTENCY_RUNS times and take median scores."""
        results: list[EvaluationResult] = []
        for i in range(SELF_CONSISTENCY_RUNS):
            try:
                r = parse_structured_output(llm, EVALUATOR_PROMPT, variables, EvaluationResult)
                results.append(r)
            except Exception as exc:
                logger.warning("Self-consistency run %d failed: %s", i + 1, exc)

        if not results:
            raise RuntimeError("All self-consistency evaluation runs failed.")

        if len(results) == 1:
            return results[0]

        # Median scores
        correctness = statistics.median(r.correctness for r in results)
        depth = statistics.median(r.depth for r in results)
        communication = statistics.median(r.communication for r in results)

        # Use the result closest to median overall as the representative
        median_overall = statistics.median(r.overall for r in results)
        representative = min(results, key=lambda r: abs(r.overall - median_overall))

        return EvaluationResult(
            correctness=round(correctness, 1),
            depth=round(depth, 1),
            communication=round(communication, 1),
            overall=round(0.4 * correctness + 0.35 * depth + 0.25 * communication, 2),
            matched_points=representative.matched_points,
            missed_points=representative.missed_points,
            red_flags=representative.red_flags,
            needs_followup=representative.needs_followup,
            followup_reason=representative.followup_reason,
        )
