"""
Report Agent
------------
Compiles a SessionReport with per-turn scores, averages, trend,
strengths, gaps, 7-day improvement plan, and benchmark comparison.
Exports Markdown and PDF to data/reports/.
"""

from __future__ import annotations

import csv
import logging
import statistics
from pathlib import Path

from config import settings
from src.memory.session_memory import SessionMemory
from src.rag.company_dna import CompanyDNABuilder
from src.schemas.models import SessionReport, TurnScore
from src.schemas.rag import CompanyDNAProfile

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(settings.archive_csv_path).parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Score verdict thresholds
THRESHOLD_SELECTED = 7.5
THRESHOLD_BORDERLINE = 6.0


class ReportAgent:
    """Compiles and exports a full session report."""

    def __init__(self, dna_builder: CompanyDNABuilder | None = None) -> None:
        self.dna_builder = dna_builder

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        memory: SessionMemory,
        dna_profile: CompanyDNAProfile | None = None,
    ) -> SessionReport:
        """Compile SessionReport, write Markdown + PDF, persist to SQLite."""
        state = memory.state
        history = state.history

        # --- Per-turn scores ---
        turn_scores: list[TurnScore] = []
        for t in history:
            if t.evaluation:
                turn_scores.append(
                    TurnScore(
                        turn_number=t.turn_number,
                        question=t.question,
                        question_id=t.question_id,
                        topic=t.topic or "",
                        round_type=t.round_type or "",
                        correctness=t.evaluation.correctness,
                        depth=t.evaluation.depth,
                        communication=t.evaluation.communication,
                        overall=t.evaluation.overall,
                        is_followup=t.is_followup,
                    )
                )

        if not turn_scores:
            # Empty session guard
            report = SessionReport(
                session_id=state.session_id,
                company=state.company,
                role=state.role,
                turn_scores=[],
                averages={"correctness": 0.0, "depth": 0.0, "communication": 0.0, "overall": 0.0},
                trend="flat",
                top_strengths=[],
                top_gaps=[],
                improvement_plan=[],
                benchmark_comparison={},
                verdict="Needs Practice",
            )
            self._export(report, memory)
            return report

        # --- Averages ---
        averages = {
            "correctness": round(statistics.mean(ts.correctness for ts in turn_scores), 2),
            "depth": round(statistics.mean(ts.depth for ts in turn_scores), 2),
            "communication": round(statistics.mean(ts.communication for ts in turn_scores), 2),
            "overall": round(statistics.mean(ts.overall for ts in turn_scores), 2),
        }

        # --- Trend ---
        trend = self._compute_trend([ts.overall for ts in turn_scores])

        # --- Strengths & Gaps ---
        matched: list[str] = []
        missed: list[str] = []
        red_flags: list[str] = []
        for t in history:
            if t.evaluation:
                matched.extend(t.evaluation.matched_points)
                missed.extend(t.evaluation.missed_points)
                red_flags.extend(t.evaluation.red_flags)

        from collections import Counter
        top_strengths = [item for item, _ in Counter(matched).most_common(3)]
        top_gaps = [item for item, _ in Counter(missed + red_flags).most_common(3)]

        # --- 7-day improvement plan ---
        topic_scores = self._topic_avg_scores(turn_scores)
        improvement_plan = self._build_improvement_plan(topic_scores)

        # --- Benchmark comparison ---
        benchmark = self._compute_benchmark(state.company, state.role)

        # --- Verdict ---
        overall_avg = averages["overall"]
        if overall_avg >= THRESHOLD_SELECTED:
            verdict = "Selected Ready"
        elif overall_avg >= THRESHOLD_BORDERLINE:
            verdict = "Borderline"
        else:
            verdict = "Needs Practice"

        report = SessionReport(
            session_id=state.session_id,
            company=state.company,
            role=state.role,
            turn_scores=turn_scores,
            averages=averages,
            trend=trend,
            top_strengths=top_strengths,
            top_gaps=top_gaps,
            improvement_plan=improvement_plan,
            benchmark_comparison=benchmark,
            verdict=verdict,
        )

        self._export(report, memory)
        return report

    # ------------------------------------------------------------------
    # Trend, strengths, improvement plan, benchmark
    # ------------------------------------------------------------------

    def _compute_trend(self, scores: list[float]) -> str:
        if len(scores) < 2:
            return "flat"
        first_half = statistics.mean(scores[: len(scores) // 2])
        second_half = statistics.mean(scores[len(scores) // 2 :])
        diff = second_half - first_half
        if diff >= 0.5:
            return "upward"
        elif diff <= -0.5:
            return "declining"
        return "flat"

    def _topic_avg_scores(self, turn_scores: list[TurnScore]) -> dict[str, float]:
        from collections import defaultdict
        topic_totals: dict[str, list[float]] = defaultdict(list)
        for ts in turn_scores:
            if ts.topic:
                topic_totals[ts.topic].append(ts.overall)
        return {topic: round(statistics.mean(vals), 2) for topic, vals in topic_totals.items()}

    def _build_improvement_plan(self, topic_scores: dict[str, float]) -> list[str]:
        """Build a 7-day plan targeting the weakest topics."""
        if not topic_scores:
            return ["Day 1-7: Review core fundamentals across all topics."]

        sorted_topics = sorted(topic_scores.items(), key=lambda kv: kv[1])
        weak_topics = [t for t, _ in sorted_topics[:3]]

        plan: list[str] = []
        resources = {
            "DSA": "LeetCode Medium problems on Arrays, Trees, Graphs",
            "DBMS": "Normalization, Indexing, SQL query practice",
            "OS": "Process scheduling, memory management, deadlock",
            "Networks": "OSI model, TCP/IP, HTTP internals",
            "System Design": "Design a URL shortener and a rate limiter",
            "OOP": "SOLID principles and design patterns (Factory, Observer)",
            "Aptitude": "Quantitative practice on percentages, ratios, time-work",
            "Behavioral": "STAR method practice with real project stories",
            "Projects": "Prepare 3-minute project walkthroughs with impact metrics",
            "Domain": "Review domain-specific concepts for the role",
        }

        day = 1
        for topic in weak_topics:
            resource = resources.get(topic, f"Core {topic} concepts")
            plan.append(f"Day {day}-{day+1}: [{topic}] {resource}")
            day += 2

        # Fill remaining days
        if day <= 7:
            plan.append(f"Day {day}-7: Mock full interview simulation + revision")

        return plan

    def _compute_benchmark(self, company: str, role: str) -> dict:
        """Read archive CSV and compute avg score_given for Selected candidates with fallback."""
        try:
            csv_path = Path(settings.archive_csv_path)
            if not csv_path.exists():
                return {}
            role_scores: list[float] = []
            company_scores: list[float] = []
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("company", "").lower() == company.lower() and row.get("outcome", "") == "Selected":
                        try:
                            score = float(row["score_given"])
                            company_scores.append(score)
                            if role and row.get("role", "").lower() == role.lower():
                                role_scores.append(score)
                        except (ValueError, KeyError):
                            pass
            scores = role_scores if role_scores else company_scores
            matched_role = role if role_scores else f"All Roles ({company})"
            if scores:
                avg = round(statistics.mean(scores), 2)
                return {
                    "company": company,
                    "role": matched_role,
                    "avg_score_selected": avg,
                    "sample_size": len(scores),
                }
        except Exception as exc:
            logger.warning("Benchmark computation failed: %s", exc)
        return {}

    # ------------------------------------------------------------------
    # Export: Markdown + PDF
    # ------------------------------------------------------------------

    def _export(self, report: SessionReport, memory: SessionMemory) -> None:
        md_path = REPORTS_DIR / f"{report.session_id}.md"
        self._write_markdown(report, md_path)

        pdf_path = REPORTS_DIR / f"{report.session_id}.pdf"
        try:
            self._write_pdf(report, pdf_path)
        except Exception as exc:
            logger.warning("PDF export failed: %s", exc)

        # Persist to SQLite
        try:
            memory.sqlite_store.save_report(report.session_id, report.model_dump())
        except Exception as exc:
            logger.warning("SQLite report save failed: %s", exc)

    def _write_markdown(self, report: SessionReport, path: Path) -> None:
        lines = [
            "# InterviewDNA Session Report",
            "",
            f"**Session ID:** {report.session_id}  ",
            f"**Company:** {report.company}  **Role:** {report.role}  ",
            f"**Verdict:** {report.verdict}",
            "",
            "## Scores",
            "",
            "| Turn | Topic | Round | Correct | Depth | Comm | Overall |",
            "|------|-------|-------|---------|-------|------|---------|",
        ]
        for ts in report.turn_scores:
            followup_mark = " ↩" if ts.is_followup else ""
            lines.append(
                f"| {ts.turn_number}{followup_mark} | {ts.topic} | {ts.round_type} "
                f"| {ts.correctness:.1f} | {ts.depth:.1f} | {ts.communication:.1f} | **{ts.overall:.1f}** |"
            )

        avg = report.averages
        lines += [
            "",
            f"**Averages:** Correctness {avg.get('correctness', 0):.1f} | "
            f"Depth {avg.get('depth', 0):.1f} | "
            f"Communication {avg.get('communication', 0):.1f} | "
            f"Overall **{avg.get('overall', 0):.1f}**",
            "",
            f"**Trend:** {report.trend.capitalize()}",
            "",
        ]

        if report.benchmark_comparison:
            bc = report.benchmark_comparison
            lines += [
                "## Benchmark Comparison",
                "",
                f"Selected candidates at **{bc.get('company')}** ({bc.get('role')}) "
                f"averaged **{bc.get('avg_score_selected', 0):.1f}/10** "
                f"(n={bc.get('sample_size', 0)}).  "
                f"Your session average: **{avg.get('overall', 0):.1f}/10**.",
                "",
            ]

        lines += [
            "## Strengths",
            "",
        ]
        for s in report.top_strengths:
            lines.append(f"- {s}")

        lines += [
            "",
            "## Gaps & Red Flags",
            "",
        ]
        for g in report.top_gaps:
            lines.append(f"- {g}")

        lines += [
            "",
            "## 7-Day Improvement Plan",
            "",
        ]
        for item in report.improvement_plan:
            lines.append(f"- {item}")

        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Markdown report written to %s", path)

    def _write_pdf(self, report: SessionReport, path: Path) -> None:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm)
        styles = getSampleStyleSheet()
        story = []

        def h1(text):
            return Paragraph(f"<b>{text}</b>", styles["Heading1"])

        def h2(text):
            return Paragraph(f"<b>{text}</b>", styles["Heading2"])

        def body(text):
            return Paragraph(text, styles["BodyText"])

        story += [
            h1("InterviewDNA Session Report"),
            body(f"<b>Session:</b> {report.session_id}"),
            body(f"<b>Company:</b> {report.company} &nbsp; <b>Role:</b> {report.role}"),
            body(f"<b>Verdict:</b> {report.verdict}"),
            Spacer(1, 0.4 * cm),
            h2("Score Table"),
        ]

        # Score table
        table_data = [["Turn", "Topic", "Round", "Correct", "Depth", "Comm", "Overall"]]
        for ts in report.turn_scores:
            followup_mark = " (FU)" if ts.is_followup else ""
            table_data.append([
                f"{ts.turn_number}{followup_mark}",
                ts.topic,
                ts.round_type,
                f"{ts.correctness:.1f}",
                f"{ts.depth:.1f}",
                f"{ts.communication:.1f}",
                f"{ts.overall:.1f}",
            ])

        t = Table(table_data, hAlign="LEFT")
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A90D9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF4FB")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(t)
        story.append(Spacer(1, 0.3 * cm))

        avg = report.averages
        story.append(
            body(
                f"<b>Averages:</b> Correctness {avg.get('correctness', 0):.1f} | "
                f"Depth {avg.get('depth', 0):.1f} | "
                f"Communication {avg.get('communication', 0):.1f} | "
                f"Overall <b>{avg.get('overall', 0):.1f}</b>"
            )
        )
        story.append(body(f"<b>Trend:</b> {report.trend.capitalize()}"))
        story.append(Spacer(1, 0.3 * cm))

        if report.benchmark_comparison:
            bc = report.benchmark_comparison
            story += [
                h2("Benchmark Comparison"),
                body(
                    f"Selected candidates at <b>{bc.get('company')}</b> ({bc.get('role')}) "
                    f"averaged <b>{bc.get('avg_score_selected', 0):.1f}/10</b> "
                    f"(n={bc.get('sample_size', 0)}).  "
                    f"Your session average: <b>{avg.get('overall', 0):.1f}/10</b>."
                ),
                Spacer(1, 0.3 * cm),
            ]

        story.append(h2("Strengths"))
        for s in report.top_strengths:
            story.append(body(f"• {s}"))
        story.append(Spacer(1, 0.2 * cm))

        story.append(h2("Gaps & Red Flags"))
        for g in report.top_gaps:
            story.append(body(f"• {g}"))
        story.append(Spacer(1, 0.2 * cm))

        story.append(h2("7-Day Improvement Plan"))
        for item in report.improvement_plan:
            story.append(body(f"• {item}"))

        doc.build(story)
        logger.info("PDF report written to %s", path)
