"""
src/api/deps.py — Shared application state and dependency providers.
"""

from __future__ import annotations

import csv
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from config import settings
from src.memory.session_memory import SessionMemory, SQLiteSessionStore
from src.orchestrator import Orchestrator
from src.rag.company_dna import CompanyDNABuilder
from src.rag.retriever import InterviewRetriever

logger = logging.getLogger(__name__)

# Global in-memory session registry (mapping session_id -> SessionMemory)
_ACTIVE_SESSIONS: dict[str, SessionMemory] = {}


def get_active_sessions() -> dict[str, SessionMemory]:
    """Returns the process-wide active sessions dictionary."""
    return _ACTIVE_SESSIONS


@lru_cache(maxsize=1)
def get_retriever() -> InterviewRetriever:
    """Returns a cached instance of InterviewRetriever."""
    return InterviewRetriever()


@lru_cache(maxsize=1)
def get_dna_builder() -> CompanyDNABuilder:
    """Returns a cached CompanyDNABuilder."""
    return CompanyDNABuilder(get_retriever())


@lru_cache(maxsize=1)
def get_sqlite_store() -> SQLiteSessionStore:
    """Returns a cached SQLiteSessionStore."""
    return SQLiteSessionStore()


@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:
    """Returns the unified orchestrator instance."""
    retriever = get_retriever()
    sqlite_store = get_sqlite_store()
    return Orchestrator(retriever=retriever, sqlite_store=sqlite_store)


@lru_cache(maxsize=1)
def load_archive_records() -> dict[str, dict[str, Any]]:
    """Loads all historical archive records indexed by record_id."""
    csv_path = Path(settings.archive_csv_path)
    records: dict[str, dict[str, Any]] = {}
    if not csv_path.exists():
        logger.warning("Archive CSV does not exist at %s", csv_path)
        return records

    try:
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rec_id = row.get("record_id", "").strip()
                if rec_id:
                    # Parse numeric fields
                    parsed: dict[str, Any] = dict(row)
                    try:
                        parsed["year"] = int(row.get("year", 0))
                    except ValueError:
                        pass
                    try:
                        parsed["difficulty"] = int(row.get("difficulty", 3))
                    except ValueError:
                        pass
                    try:
                        parsed["score_given"] = float(row.get("score_given", 0.0))
                    except ValueError:
                        pass
                    if "feedback_tags" in row and isinstance(row["feedback_tags"], str):
                        parsed["feedback_tags"] = [
                            t.strip() for t in row["feedback_tags"].split("|") if t.strip()
                        ]
                    if "expected_points" in row and isinstance(row["expected_points"], str):
                        parsed["expected_points"] = [
                            p.strip() for p in row["expected_points"].split("|") if p.strip()
                        ]
                    records[rec_id] = parsed
    except Exception as exc:
        logger.error("Failed to load archive CSV: %s", exc)

    logger.info("Loaded %d archive records into memory cache", len(records))
    return records


def get_archive_record_by_id(record_id: str) -> dict[str, Any] | None:
    """Retrieves a single archive record by record_id."""
    records = load_archive_records()
    return records.get(record_id.strip())
