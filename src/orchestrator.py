"""
Orchestrator
------------
Coordinates intent routing, session memory, and agent dispatch.
Provides a unified handle_message() interface for the UI or CLI.
"""

from __future__ import annotations

import logging
from typing import Any

from src.agents.coach import CoachAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.interviewer import InterviewerAgent
from src.agents.report import ReportAgent
from src.memory.session_memory import SessionMemory, SQLiteSessionStore
from src.rag.company_dna import CompanyDNABuilder
from src.rag.retriever import InterviewRetriever
from src.router.intent_router import IntentRouter
from src.schemas.models import (
    CoachingAdvice,
    EvaluationResult,
    InterviewState,
    SessionReport,
    TurnRecord,
)
from src.schemas.router import IntentType

logger = logging.getLogger(__name__)


class Orchestrator:
    """Central coordinator for InterviewDNA."""

    def __init__(
        self,
        retriever: InterviewRetriever | None = None,
        sqlite_store: SQLiteSessionStore | None = None,
        interviewer: InterviewerAgent | None = None,
        evaluator: EvaluatorAgent | None = None,
        coach: CoachAgent | None = None,
        report_agent: ReportAgent | None = None,
        router: IntentRouter | None = None,
    ) -> None:
        self.retriever = retriever or InterviewRetriever()
        self.dna_builder = CompanyDNABuilder(self.retriever)
        self.sqlite_store = sqlite_store or SQLiteSessionStore()

        self.interviewer = interviewer or InterviewerAgent(self.retriever, self.dna_builder)
        self.evaluator = evaluator or EvaluatorAgent()
        self.coach = coach or CoachAgent(self.retriever)
        self.report_agent = report_agent or ReportAgent(self.dna_builder)
        self.router = router or IntentRouter()

    def get_or_create_session(
        self,
        session_id: str,
        sessions_dict: dict[str, SessionMemory],
        company: str = "Zoho",
        role: str = "Software Development Engineer",
        user_nickname: str = "Student",
    ) -> SessionMemory:
        """Retrieve existing session memory or create a new one."""
        if session_id not in sessions_dict:
            initial_state = InterviewState(
                session_id=session_id,
                company=company,
                role=role,
                user_nickname=user_nickname,
                round_type="Aptitude",
            )
            memory = SessionMemory(
                initial_state=initial_state,
                sqlite_store=self.sqlite_store,
            )
            sessions_dict[session_id] = memory
        return sessions_dict[session_id]

    def handle_message(
        self,
        session_id: str,
        user_message: str,
        sessions_dict: dict[str, SessionMemory],
        company: str = "Zoho",
        role: str = "Software Development Engineer",
        user_nickname: str = "Student",
    ) -> dict[str, Any]:
        """
        Process a user message and route to the appropriate agent.

        Returns:
            dict containing:
                - response: str (markdown formatted response)
                - routing: RoutingDecision
                - evaluation: Optional[EvaluationResult]
                - report: Optional[SessionReport]
                - turn: Optional[TurnRecord]
        """
        memory = self.get_or_create_session(
            session_id=session_id,
            sessions_dict=sessions_dict,
            company=company,
            role=role,
            user_nickname=user_nickname,
        )

        # 1. Routing
        routing = self.router.classify_intent(
            message=user_message,
            has_pending_question=memory.has_pending_question,
        )
        logger.info(
            "Routing [%s]: intent=%s agent=%s confidence=%.2f",
            session_id,
            routing.intent,
            routing.target_agent,
            routing.confidence,
        )

        response_text = ""
        evaluation_result: EvaluationResult | None = None
        session_report: SessionReport | None = None
        turn_record: TurnRecord | None = None
        coaching_advice: CoachingAdvice | None = None

        # 2. Dispatch
        if routing.intent == IntentType.EVALUATE:
            if not memory.has_pending_question:
                # No active question to answer, treat as smalltalk or prompt practice
                response_text = (
                    "You don't have a pending question to answer. "
                    "Type **'next question'** or **'start practice'** to receive a question!"
                )
            else:
                active_turn = memory.get_active_turn()
                evaluation_result = self.evaluator.run(
                    candidate_answer=user_message,
                    turn=active_turn,
                    memory=memory,
                )

                # Format evaluation display
                eval_md = self._format_evaluation(evaluation_result)

                # Check if adaptive follow-up is needed
                if evaluation_result.needs_followup and memory.state.followup_count < 1:
                    fu_turn = self.interviewer.generate_followup(memory, evaluation_result)
                    turn_record = fu_turn
                    response_text = (
                        f"{eval_md}\n\n"
                        f"### 🔍 Follow-Up Question\n"
                        f"*(Focusing on: {evaluation_result.followup_reason or 'clarification'})*\n\n"
                        f"**{fu_turn.question}**"
                    )
                else:
                    # Provide next question automatically
                    next_turn = self.interviewer.run(memory)
                    turn_record = next_turn
                    response_text = (
                        f"{eval_md}\n\n"
                        f"---\n\n"
                        f"### 🎯 Next Question (Round: {next_turn.round_type} | Topic: {next_turn.topic})\n\n"
                        f"**{next_turn.question}**"
                    )

        elif routing.intent == IntentType.PRACTICE:
            next_turn = self.interviewer.run(memory)
            turn_record = next_turn
            response_text = (
                f"### 🎯 Question #{next_turn.turn_number} "
                f"({next_turn.round_type} Round | {next_turn.topic})\n\n"
                f"**{next_turn.question}**\n\n"
                f"*Type your answer below when ready.*"
            )

        elif routing.intent == IntentType.COACH:
            coaching_advice = self.coach.run(memory, query=user_message)
            response_text = self._format_coaching(coaching_advice)

        elif routing.intent == IntentType.REPORT:
            dna = self.dna_builder.get_or_build(memory.state.company, memory.state.role)
            session_report = self.report_agent.run(memory, dna_profile=dna)
            response_text = self._format_report_summary(session_report)

        else:  # SMALLTALK_OR_UNCLEAR
            response_text = (
                "👋 Hello! I am **InterviewDNA**, your company-smart mock interview coach.\n\n"
                f"Currently configured for **{memory.state.company}** - **{memory.state.role}**.\n\n"
                "Here is what you can do:\n"
                "- Type **'start'** or **'next question'** to practice real questions.\n"
                "- Submit your answer to receive an instant rubric evaluation.\n"
                "- Ask for **'coaching'** or **'tips on DBMS'** to see grounded historical advice with record citations.\n"
                "- Type **'generate report'** or **'end interview'** to download your PDF scorecard and 7-day study plan."
            )

        return {
            "response": response_text,
            "routing": routing,
            "evaluation": evaluation_result,
            "report": session_report,
            "turn": turn_record,
            "coaching": coaching_advice,
        }

    # ------------------------------------------------------------------
    # Formatting Helpers
    # ------------------------------------------------------------------

    def _format_evaluation(self, eval_res: EvaluationResult) -> str:
        lines = [
            f"### 📊 Answer Evaluation (Overall: {eval_res.overall:.1f}/10)",
            "",
            f"- **Correctness**: {eval_res.correctness:.1f}/10",
            f"- **Depth & Complexity**: {eval_res.depth:.1f}/10",
            f"- **Communication**: {eval_res.communication:.1f}/10",
        ]
        if eval_res.matched_points:
            lines.append("\n**✅ What you covered:**")
            for p in eval_res.matched_points:
                lines.append(f"- {p}")
        if eval_res.missed_points:
            lines.append("\n**⚠️ What was missed:**")
            for p in eval_res.missed_points:
                lines.append(f"- {p}")
        if eval_res.red_flags:
            lines.append("\n**🚩 Red Flags / Gaps:**")
            for rf in eval_res.red_flags:
                lines.append(f"- {rf}")
        return "\n".join(lines)

    def _format_coaching(self, advice: Any) -> str:
        lines = [
            "### 💡 Company-Grounded Coaching Advice",
            "",
            f"**Summary:** {advice.summary}",
            "",
        ]
        if advice.no_evidence_notice:
            lines.append(f"> ⚠️ *{advice.no_evidence_notice}*\n")

        lines.append("#### Key Actionable Tips:")
        for idx, tip in enumerate(advice.tips, 1):
            cites = ""
            if tip.evidence_ids:
                if isinstance(tip.evidence_year, (list, tuple)):
                    years = f" ({', '.join(str(y) for y in tip.evidence_year)})"
                elif tip.evidence_year:
                    years = f" ({tip.evidence_year})"
                else:
                    years = ""
                cites = f" *(Evidence: {', '.join(tip.evidence_ids)}{years})*"
            lines.append(f"{idx}. {tip.text}{cites}")

        return "\n".join(lines)

    def _format_report_summary(self, report: SessionReport) -> str:
        avg = report.averages
        lines = [
            "### 🎓 InterviewDNA Session Complete!",
            "",
            f"**Verdict:** {report.verdict}  |  **Overall Average:** {avg.get('overall', 0):.1f}/10  |  **Trend:** {report.trend.capitalize()}",
            "",
            f"- **Correctness:** {avg.get('correctness', 0):.1f}/10",
            f"- **Depth:** {avg.get('depth', 0):.1f}/10",
            f"- **Communication:** {avg.get('communication', 0):.1f}/10",
            "",
        ]
        if report.benchmark_comparison:
            bc = report.benchmark_comparison
            lines.append(
                f"**Benchmark:** Candidates selected at {bc.get('company')} average "
                f"**{bc.get('avg_score_selected', 0):.1f}/10** (n={bc.get('sample_size', 0)}).\n"
            )

        if report.top_strengths:
            lines.append(f"**Top Strengths:** {', '.join(report.top_strengths)}")
        if report.top_gaps:
            lines.append(f"**Key Gaps to Address:** {', '.join(report.top_gaps)}")

        if report.improvement_plan:
            lines.append("\n**📅 7-Day Improvement Plan:**")
            for day in report.improvement_plan:
                lines.append(f"- {day}")

        lines.append(
            f"\n📄 *Detailed reports generated in `data/reports/`:*\n"
            f"- Markdown: `data/reports/{report.session_id}.md`\n"
            f"- PDF: `data/reports/{report.session_id}.pdf`"
        )
        return "\n".join(lines)
