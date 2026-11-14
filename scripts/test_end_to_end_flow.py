"""
scripts/test_end_to_end_flow.py
-------------------------------
End-to-end integration and smoke test running the full InterviewDNA pipeline
across two distinct companies (Zoho and Amazon) without requiring a paid LLM key.
Uses FakeListChatModel for predictable LLM responses while exercising real ChromaDB,
real SQLite persistence, real Company DNA computations, and real PDF/Markdown report generation.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from rich.console import Console
from rich.panel import Panel

from src.memory.session_memory import SQLiteSessionStore
from src.orchestrator import Orchestrator
from src.rag.company_dna import build_company_dna
from src.rag.retriever import InterviewRetriever

console = Console()
logging.basicConfig(level=logging.INFO)


def run_company_flow(company: str, role: str, session_id: str, sample_answers: list[str]):
    console.print(Panel(f"[bold cyan]Testing Full End-to-End Flow for: {company} ({role})[/]", border_style="cyan"))

    retriever = InterviewRetriever()
    sqlite_store = SQLiteSessionStore()
    orchestrator = Orchestrator(retriever=retriever, sqlite_store=sqlite_store)

    # 1. Inspect Company DNA
    dna = build_company_dna(company, role)
    console.print(f"📊 [bold]Company DNA Profile:[/] Selection Rate = {dna.selection_rate}%, Avg Difficulty = {dna.avg_difficulty}")
    console.print(f"   Top Rejection: [red]{dna.top_rejection_tags[0]['tag']}[/] ({dna.top_rejection_tags[0]['count']} candidates)")
    console.print(f"   Top Strength: [green]{dna.top_positive_tags[0]['tag']}[/] ({dna.top_positive_tags[0]['count']} candidates)")

    sessions = {}
    memory = orchestrator.get_or_create_session(
        session_id=session_id,
        sessions_dict=sessions,
        company=company,
        role=role,
        user_nickname="TestCandidate",
    )

    # Mock Interviewer & Evaluator LLMs
    fake_eval_json_1 = json.dumps({
        "correctness": 8.5,
        "depth": 8.0,
        "communication": 8.5,
        "overall": 8.3,
        "matched_points": ["Solid conceptual breakdown", "Accurate complexity analysis", "Clear STAR structure" if company == "Amazon" else "Good data structures choice"],
        "missed_points": ["Could explain secondary trade-offs"],
        "red_flags": [],
        "needs_followup": False,
        "followup_reason": None,
    })

    fake_eval_json_2 = json.dumps({
        "correctness": 9.0,
        "depth": 9.0,
        "communication": 8.5,
        "overall": 8.9,
        "matched_points": ["Optimal space-time trade-off", "Clear communication", "Addressed edge cases"],
        "missed_points": [],
        "red_flags": [],
        "needs_followup": False,
        "followup_reason": None,
    })

    fake_eval_llm = FakeListChatModel(responses=[fake_eval_json_1, fake_eval_json_2])
    orchestrator.evaluator = orchestrator.evaluator.__class__(self_consistency=False)
    # Monkeypatch evaluator
    import src.agents.evaluator as ev_mod
    ev_mod.get_llm = lambda **kwargs: fake_eval_llm

    # 2. Turn 1: Ask Question
    t1 = orchestrator.interviewer.run(memory)
    console.print(f"\n[bold yellow]Turn 1 Question ({t1.round_type} Round | {t1.topic}):[/]\n{t1.question}")

    # 3. Turn 1: Submit Answer & Evaluate
    ans1 = sample_answers[0]
    console.print(f"\n[bold green]Candidate Answer 1:[/] {ans1}")
    res_eval1 = orchestrator.evaluator.run(candidate_answer=ans1, turn=t1, memory=memory)
    console.print(f"✅ [bold]Evaluation 1:[/] Score={res_eval1.overall}/10 | Correctness={res_eval1.correctness} | Depth={res_eval1.depth} | Comm={res_eval1.communication}")

    # 4. Turn 2: Ask Question (Adaptive Difficulty Check)
    t2 = orchestrator.interviewer.run(memory)
    console.print(f"\n[bold yellow]Turn 2 Question ({t2.round_type} Round | {t2.topic} | Difficulty Level {memory.state.difficulty_level}/5):[/]\n{t2.question}")

    # 5. Turn 2: Submit Answer & Evaluate
    ans2 = sample_answers[1]
    console.print(f"\n[bold green]Candidate Answer 2:[/] {ans2}")
    res_eval2 = orchestrator.evaluator.run(candidate_answer=ans2, turn=t2, memory=memory)
    console.print(f"✅ [bold]Evaluation 2:[/] Score={res_eval2.overall}/10 | Correctness={res_eval2.correctness} | Depth={res_eval2.depth} | Comm={res_eval2.communication}")

    # 6. Coaching Advice Retrieval
    fb_res = retriever.get_feedback(company=company, role=role, query=f"How to prepare for {company}", k=3)
    rec_id = fb_res.items[0].record_id if fb_res.items else f"{company[:3].upper()}-2024-001"
    yr = fb_res.items[0].year if fb_res.items else 2024

    fake_coach_json = json.dumps({
        "summary": f"Historical candidates at {company} succeed by demonstrating rigorous problem solving and structured communication.",
        "tips": [
            {
                "text": f"Prioritize writing syntax-free code and analyzing asymptotic bounds early, as {company} interviewers heavily penalize hand-waving.",
                "evidence_ids": [rec_id],
                "evidence_year": yr,
            }
        ],
        "no_evidence_notice": None,
    })
    import src.agents.coach as coach_mod
    coach_mod.get_llm = lambda **kwargs: FakeListChatModel(responses=[fake_coach_json])

    advice = orchestrator.coach.run(memory, query=f"What does {company} look for?")
    console.print(f"\n💡 [bold]Coach Advice Summary:[/] {advice.summary}")
    for idx, tip in enumerate(advice.tips, 1):
        console.print(f"   Tip {idx}: {tip.text} [bold cyan](Evidence: {tip.evidence_ids}, {tip.evidence_year})[/]")

    # 7. Generate Final Report (Markdown + PDF)
    report = orchestrator.report_agent.run(memory, dna_profile=dna)
    console.print(f"\n🎓 [bold]Final Session Report:[/] Verdict = [bold green]{report.verdict}[/], Overall Average = {report.averages.get('overall')}/10")
    console.print(f"   Benchmark Selected Avg at {company}: {report.benchmark_comparison.get('avg_score_selected')}/10")
    console.print(f"   Top Strengths: {', '.join(report.top_strengths)}")
    console.print(f"   Improvement Roadmap: {report.improvement_plan[0] if report.improvement_plan else 'N/A'}")

    md_path = Path("data/reports") / f"{session_id}.md"
    pdf_path = Path("data/reports") / f"{session_id}.pdf"
    assert md_path.exists(), f"Markdown report not found at {md_path}"
    assert pdf_path.exists(), f"PDF report not found at {pdf_path}"
    console.print(f"📄 Generated Reports: {md_path} ({md_path.stat().st_size} bytes), {pdf_path} ({pdf_path.stat().st_size} bytes)")
    return dna, report


def main():
    console.print("[bold blue]Starting Full InterviewDNA End-to-End Multi-Company Flow Verification...[/]\n")

    # Flow 1: Zoho (DSA & Technical focus)
    zoho_dna, zoho_rep = run_company_flow(
        company="Zoho",
        role="Software Development Engineer",
        session_id="test_zoho_e2e_01",
        sample_answers=[
            "For finding pairs in an array summing to target, I sort the array in O(N log N) and use two pointers meeting in the middle in O(N) time and O(1) extra space.",
            "In normalized DBMS schemas, B+ trees provide O(log N) balanced lookup with leaf pointers facilitating range scans, while ACID isolation prevents dirty reads via row-level locks.",
        ],
    )

    console.print("\n" + "=" * 80 + "\n")

    # Flow 2: Amazon (Leadership Principles, System Design, Behavioral focus)
    amazon_dna, amazon_rep = run_company_flow(
        company="Amazon",
        role="Software Development Engineer",
        session_id="test_amazon_e2e_01",
        sample_answers=[
            "Using the STAR method: Situation was an outage in our payment service during Prime Day. Task was to triage and restore latency. Action: I analyzed metrics, found a database connection leak, and deployed an immediate connection pooling patch. Result: P99 latency dropped from 4s to 85ms with zero transaction loss.",
            "For rate limiting 100k requests/sec across distributed microservices, I would implement a Token Bucket algorithm backed by Redis with sliding window counters and local in-memory caching to avoid round-trip bottlenecks.",
        ],
    )

    console.print("\n" + "=" * 80 + "\n")
    console.print("[bold green]✅ Both Company End-to-End Flows Completed Successfully![/]")
    console.print(f"Zoho Selection Rate: {zoho_dna.selection_rate}% vs Amazon Selection Rate: {amazon_dna.selection_rate}%")


if __name__ == "__main__":
    main()
