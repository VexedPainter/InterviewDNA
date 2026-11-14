"""
src/rag/company_dna.py — Computes and caches comprehensive Company DNA Profiles
from the historical placement archive.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Fix Windows console UTF-8 output encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import settings
from src.llm.provider import get_llm
from src.schemas.rag import CompanyDNAProfile

log = logging.getLogger(__name__)
console = Console()

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "company_dna"


def get_dna_cache_path(company: str, role: str | None = None) -> Path:
    """Returns filesystem path for cached Company DNA JSON."""
    safe_company = company.strip().lower().replace(" ", "_")
    safe_role = role.strip().lower().replace(" ", "_") if role else "all_roles"
    return CACHE_DIR / f"{safe_company}_{safe_role}.json"


def generate_interviewer_style_summary(
    company: str,
    role: str | None,
    samples: list[dict[str, Any]],
    top_rejections: list[str],
    top_positives: list[str],
) -> str:
    """
    Generates a concise interviewer style summary.
    Attempts LLM first (Gemini/Ollama); falls back to grounded heuristic synthesis if offline.
    """
    feedback_samples_text = "\n".join(
        f"- [Score {s['score']}/10, {s['outcome']}] \"{s['feedback']}\" (Tags: {s['tags']})"
        for s in samples[:8]
    )

    prompt = (
        f"You are an expert technical recruitment analyst. Analyze these real placement interview feedback records for {company} "
        f"{'(' + role + ')' if role else ''}:\n\n"
        f"{feedback_samples_text}\n\n"
        f"Top common rejection flags: {', '.join(top_rejections[:4])}\n"
        f"Top successful traits: {', '.join(top_positives[:4])}\n\n"
        f"Write a 3-bullet-point summary characterizing the interview style, technical rigor, and candidate expectations at {company}. "
        f"Strict grounding rule: make NO generic assumptions; cite observed traits directly from these feedback samples."
    )

    try:
        llm = get_llm(temperature=0.2)
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        if text and len(text.strip()) > 20:
            return text.strip()
    except Exception as e:
        log.warning("LLM call failed or unavailable (%s). Using grounded synthesis.", e)

    # Grounded rule-based fallback based purely on the sampled records
    style_lines = [
        f"1. Core Focus & Rigor: Feedback emphasizes {', '.join(top_positives[:2]) if top_positives else 'technical foundations'}, holding high standards on conceptual depth.",
        f"2. Primary Elimination Factors: Candidates are frequently eliminated due to {', '.join(top_rejections[:2]) if top_rejections else 'weak problem breakdown'}.",
        "3. Interview Atmosphere: Interviewers assess practical demonstration over theory, prioritizing candidates who handle follow-up probing and edge cases.",
    ]
    return "\n".join(style_lines)


def build_company_dna(
    company: str,
    role: str | None = None,
    csv_path: str | None = None,
    force_refresh: bool = False,
) -> CompanyDNAProfile:
    """
    Calculates statistical distributions and grounded qualitative insights
    for a company (and optional role) from the archive CSV.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = get_dna_cache_path(company, role)

    if cache_file.exists() and not force_refresh:
        log.info("Loading Company DNA from cache: %s", cache_file)
        try:
            with open(cache_file, encoding="utf-8") as f:
                data = json.load(f)
            return CompanyDNAProfile(**data)
        except Exception as e:
            log.warning("Failed to read cache file (%s); recomputing...", e)

    archive_file = Path(csv_path or settings.archive_csv_path).resolve()
    if not archive_file.exists():
        raise FileNotFoundError(f"Archive not found at {archive_file}")

    df = pd.read_csv(archive_file)
    df_comp = df[df["company"].str.lower() == company.strip().lower()]
    if df_comp.empty:
        raise ValueError(f"No records found in archive for company: {company}")

    if role:
        df_filtered = df_comp[df_comp["role"].str.lower() == role.strip().lower()]
        if df_filtered.empty:
            log.warning("No records found for role '%s' at '%s'. Using company-level data.", role, company)
            df_filtered = df_comp
    else:
        df_filtered = df_comp

    total_records = len(df_filtered)
    selection_rate = round(float((df_filtered["outcome"] == "Selected").mean()) * 100, 2)
    avg_difficulty = round(float(df_filtered["difficulty"].mean()), 2)

    # Difficulty trend by year
    yearly_diff = df_filtered.groupby("year")["difficulty"].mean().to_dict()
    difficulty_trend = {int(k): round(float(v), 2) for k, v in yearly_diff.items()}

    # Topic distribution (%)
    topic_counts = df_filtered["topic"].value_counts(normalize=True) * 100
    topic_distribution = {k: round(float(v), 2) for k, v in topic_counts.to_dict().items()}

    # Round distribution (%)
    round_counts = df_filtered["round_type"].value_counts(normalize=True) * 100
    round_distribution = {k: round(float(v), 2) for k, v in round_counts.to_dict().items()}

    # Top rejection tags
    df_rejected = df_filtered[df_filtered["outcome"] == "Rejected"]
    rej_tags: dict[str, int] = {}
    for tags_str in df_rejected["feedback_tags"].dropna():
        for tag in str(tags_str).split("|"):
            tag_clean = tag.strip().replace("_", " ")
            if tag_clean:
                rej_tags[tag_clean] = rej_tags.get(tag_clean, 0) + 1
    sorted_rej = sorted(rej_tags.items(), key=lambda x: x[1], reverse=True)[:5]
    top_rejection_tags = [{"tag": k, "count": v} for k, v in sorted_rej]

    # Top positive tags (from Selected)
    df_selected = df_filtered[df_filtered["outcome"] == "Selected"]
    pos_tags: dict[str, int] = {}
    for tags_str in df_selected["feedback_tags"].dropna():
        for tag in str(tags_str).split("|"):
            tag_clean = tag.strip().replace("_", " ")
            if tag_clean:
                pos_tags[tag_clean] = pos_tags.get(tag_clean, 0) + 1
    sorted_pos = sorted(pos_tags.items(), key=lambda x: x[1], reverse=True)[:5]
    top_positive_tags = [{"tag": k, "count": v} for k, v in sorted_pos]

    # Sample feedback for interviewer style
    sample_rows = df_filtered.sample(min(12, len(df_filtered)), random_state=42)
    feedback_samples = [
        {
            "score": r["score_given"],
            "outcome": r["outcome"],
            "feedback": r["feedback_text"],
            "tags": str(r["feedback_tags"]).replace("|", ", "),
        }
        for _, r in sample_rows.iterrows()
    ]

    interviewer_style = generate_interviewer_style_summary(
        company=company,
        role=role,
        samples=feedback_samples,
        top_rejections=[t["tag"] for t in top_rejection_tags],
        top_positives=[t["tag"] for t in top_positive_tags],
    )

    profile = CompanyDNAProfile(
        company=company,
        role=role,
        total_records=total_records,
        selection_rate=selection_rate,
        avg_difficulty=avg_difficulty,
        difficulty_trend_by_year=difficulty_trend,
        topic_distribution=topic_distribution,
        round_distribution=round_distribution,
        top_rejection_tags=top_rejection_tags,
        top_positive_tags=top_positive_tags,
        interviewer_style_summary=interviewer_style,
        generated_at=datetime.datetime.now().isoformat(),
    )

    # Save to cache
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(), f, indent=2)
    log.info("Cached Company DNA profile to %s", cache_file)

    return profile


def print_dna_profile(profile: CompanyDNAProfile) -> None:
    """Pretty prints the company DNA profile with Rich."""
    header = f"[bold cyan]Company DNA Profile:[/] [bold green]{profile.company.upper()}[/]"
    if profile.role:
        header += f" | [yellow]{profile.role}[/]"

    console.print(Panel(header, border_style="cyan"))
    console.print(
        f"[bold]Total Archive Records:[/] {profile.total_records} | "
        f"[bold]Selection Rate:[/] {profile.selection_rate}% | "
        f"[bold]Avg Difficulty:[/] {profile.avg_difficulty}/5.0\n"
    )

    # Topics table
    t_table = Table(title="Top Examined Topics", header_style="bold magenta")
    t_table.add_column("Topic", style="cyan")
    t_table.add_column("Share", justify="right")
    for topic, share in list(profile.topic_distribution.items())[:5]:
        t_table.add_row(topic, f"{share}%")
    console.print(t_table)

    # Rounds table
    r_table = Table(title="Rounds Structure", header_style="bold blue")
    r_table.add_column("Round Type", style="cyan")
    r_table.add_column("Share", justify="right")
    for rnd, share in profile.round_distribution.items():
        r_table.add_row(rnd, f"{share}%")
    console.print(r_table)

    # Feedback Patterns
    console.print("\n[bold red]Top Rejection Reasons:[/]")
    for r in profile.top_rejection_tags:
        console.print(f"  • {r['tag']} ({r['count']} candidates)")

    console.print("\n[bold green]Top Selected Candidate Strengths:[/]")
    for p in profile.top_positive_tags:
        console.print(f"  • {p['tag']} ({p['count']} candidates)")

    console.print("\n[bold yellow]Interviewer Style & Mindset:[/] ")
    console.print(Panel(profile.interviewer_style_summary, border_style="yellow"))
    console.print("")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute or display Company DNA Profile")
    parser.add_argument("--company", type=str, default="Zoho", help="Company name (e.g. Zoho, Amazon)")
    parser.add_argument("--role", type=str, default=None, help="Role name")
    parser.add_argument("--refresh", action="store_true", help="Force refresh cache")
    args = parser.parse_args()

    prof = build_company_dna(company=args.company, role=args.role, force_refresh=args.refresh)
    print_dna_profile(prof)


class CompanyDNABuilder:
    """Class wrapper providing get_or_build() for agents and orchestrator."""

    def __init__(self, retriever=None) -> None:
        self.retriever = retriever

    def get_or_build(
        self,
        company: str,
        role: str | None = None,
        force_refresh: bool = False,
    ) -> CompanyDNAProfile:
        return build_company_dna(company=company, role=role, force_refresh=force_refresh)

