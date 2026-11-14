"""
UI Helper functions and archive lookup utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from config import settings


@st.cache_data
def load_archive_df() -> pd.DataFrame:
    """Loads and caches the full 10-year interview archive."""
    csv_path = Path(settings.archive_csv_path)
    if not csv_path.exists():
        return pd.DataFrame()
    return pd.read_csv(csv_path)


@st.cache_data
def get_record_by_id(record_id: str) -> dict[str, Any] | None:
    """Retrieves full details for a specific historical record ID."""
    df = load_archive_df()
    if df.empty or "record_id" not in df.columns:
        return None
    matched = df[df["record_id"].str.strip() == record_id.strip()]
    if matched.empty:
        return None
    return matched.iloc[0].to_dict()


def format_agent_badge(agent_name: str, confidence: float, fallback: str = "none") -> str:
    """Generates an HTML badge for agent traces."""
    colors = {
        "Interviewer Agent": ("#E0F2FE", "#0369A1"),
        "Evaluator Agent": ("#FEF3C7", "#B45309"),
        "Coach Agent": ("#DCFCE7", "#15803D"),
        "Report Agent": ("#F3E8FF", "#6B21A8"),
        "General Chat": ("#F1F5F9", "#475569"),
    }
    bg, fg = colors.get(agent_name, ("#F1F5F9", "#475569"))
    return (
        f'<span style="background-color: {bg}; color: {fg}; padding: 3px 8px; '
        f'border-radius: 12px; font-weight: 600; font-size: 0.78rem;">'
        f'{agent_name} ({int(confidence * 100)}%)'
        f'</span>'
    )
