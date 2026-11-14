"""
scripts/data_quality_report.py
================================
Reads data/interview_archive.csv and prints a structured quality report
covering row counts, breakdowns, and sanity checks.

Run:
    python scripts/data_quality_report.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Fix Windows console UTF-8 output encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from rich import box
from rich.console import Console
from rich.table import Table

ARCHIVE_PATH = Path(__file__).resolve().parents[1] / "data" / "interview_archive.csv"

console = Console(force_terminal=True, legacy_windows=False)


def load_df() -> pd.DataFrame:
    if not ARCHIVE_PATH.exists():
        console.print(f"[bold red]ERROR:[/] Archive not found at {ARCHIVE_PATH}")
        console.print("Run: [bold]python scripts/generate_synthetic_archive.py[/]")
        sys.exit(1)
    df = pd.read_csv(ARCHIVE_PATH)
    return df


def print_header(df: pd.DataFrame) -> None:
    console.rule("[bold cyan]InterviewDNA -- Data Quality Report[/]")
    console.print(f"\n[bold]Archive:[/] {ARCHIVE_PATH}")
    console.print(f"[bold]Total rows:[/] [green]{len(df):,}[/]")
    console.print(f"[bold]Columns:[/] {len(df.columns)}")
    console.print(f"[bold]Year range:[/] {df['year'].min()} - {df['year'].max()}\n")


def print_table(title: str, counts: pd.Series, col_name: str) -> None:
    table = Table(title=title, box=box.SIMPLE_HEAVY, header_style="bold magenta")
    table.add_column(col_name, style="cyan", no_wrap=True)
    table.add_column("Count", justify="right")
    table.add_column("% of Total", justify="right")
    total = counts.sum()
    for label, count in counts.items():
        pct = f"{100 * count / total:.1f}%"
        table.add_row(str(label), str(count), pct)
    console.print(table)


def print_cross_table(title: str, df: pd.DataFrame, row_col: str, col_col: str) -> None:
    pivot = df.groupby([row_col, col_col]).size().unstack(fill_value=0)
    table = Table(title=title, box=box.SIMPLE_HEAVY, header_style="bold magenta")
    table.add_column(row_col, style="cyan", no_wrap=True)
    for c in pivot.columns:
        table.add_column(str(c), justify="right")
    for idx, row in pivot.iterrows():
        table.add_row(str(idx), *[str(v) for v in row])
    console.print(table)


def print_score_stats(df: pd.DataFrame) -> None:
    table = Table(title="Score Statistics by Company", box=box.SIMPLE_HEAVY, header_style="bold magenta")
    table.add_column("Company", style="cyan")
    table.add_column("Mean Score", justify="right")
    table.add_column("Std Dev", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Selection %", justify="right")
    for company, grp in df.groupby("company"):
        mean = f"{grp['score_given'].mean():.2f}"
        std = f"{grp['score_given'].std():.2f}"
        mn = f"{grp['score_given'].min():.1f}"
        mx = f"{grp['score_given'].max():.1f}"
        sel_pct = f"{100 * (grp['outcome'] == 'Selected').sum() / len(grp):.1f}%"
        table.add_row(str(company), mean, std, mn, mx, sel_pct)
    console.print(table)


def print_null_check(df: pd.DataFrame) -> None:
    nulls = df.isnull().sum()
    has_nulls = nulls[nulls > 0]
    if has_nulls.empty:
        console.print("[bold green][OK] No NULL values found in any column.[/]\n")
    else:
        console.print("[bold red][WARNING] NULL values detected:[/]")
        console.print(has_nulls.to_string())


def print_difficulty_distribution(df: pd.DataFrame) -> None:
    table = Table(title="Difficulty Distribution by Company (count)", box=box.SIMPLE_HEAVY, header_style="bold magenta")
    pivot = df.groupby(["company", "difficulty"]).size().unstack(fill_value=0)
    table.add_column("Company", style="cyan")
    for d in sorted(pivot.columns):
        table.add_column(f"Diff {d}", justify="right")
    for company, row in pivot.iterrows():
        table.add_row(str(company), *[str(row.get(d, 0)) for d in sorted(pivot.columns)])
    console.print(table)


def print_unique_questions(df: pd.DataFrame) -> None:
    total = len(df)
    unique_q = df["question"].nunique()
    console.print(f"[bold]Unique questions:[/] [green]{unique_q}[/] out of {total} rows")
    console.print(f"[bold]Question reuse rate:[/] {100*(total-unique_q)/total:.1f}% (expected -- same Q asked across different candidates)\n")


def run_report() -> None:
    df = load_df()
    print_header(df)
    print_null_check(df)
    print_unique_questions(df)

    print_table("Rows by Company", df["company"].value_counts().sort_index(), "Company")
    print_table("Rows by Year", df["year"].value_counts().sort_index(), "Year")
    print_table("Rows by Round Type", df["round_type"].value_counts(), "Round Type")
    print_table("Rows by Topic", df["topic"].value_counts(), "Topic")
    print_table("Rows by Outcome", df["outcome"].value_counts(), "Outcome")

    print_cross_table("Round Type x Company", df, "round_type", "company")
    print_cross_table("Topic x Company", df, "topic", "company")

    print_difficulty_distribution(df)
    print_score_stats(df)

    console.rule("[bold cyan]End of Report[/]")


if __name__ == "__main__":
    run_report()
