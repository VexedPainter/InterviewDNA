"""
src/memory/session_memory.py — Dual-tier memory architecture for InterviewDNA.

Tiers:
1. Short-Term Memory: In-memory LangChain-compatible conversation history,
   tracking active company, role, asked question IDs, turn evaluations,
   and dynamic history condensation when exceeding N turns.
2. Long-Term Memory: SQLite persistence (data/sessions.db) storing sessions,
   turns, scores, and reports identified by user nickname (no authentication needed).
"""

from __future__ import annotations

import datetime
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from config import settings
from src.schemas.models import (
    EvaluationResult,
    InterviewState,
    SessionReport,
    TurnRecord,
)

log = logging.getLogger(__name__)


# ==============================================================================
# SQLite Database Manager (Long-Term Storage)
# ==============================================================================

class SQLiteSessionStore:
    """Manages persistent SQLite tables for sessions, turns, and reports."""

    def __init__(self, db_path: str | None = None):
        # For in-memory databases, we must reuse the same connection object
        # because a new sqlite3.connect(":memory:") call creates a *different*
        # ephemeral database — tables created on one connection don't exist on another.
        if db_path == ":memory:":
            self.db_path = ":memory:"
            self._memory_conn: sqlite3.Connection | None = sqlite3.connect(
                ":memory:", check_same_thread=False
            )
            self._memory_conn.row_factory = sqlite3.Row
        else:
            p = Path(db_path or settings.sqlite_db_path).resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            self.db_path = str(p)
            self._memory_conn = None
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        if self._memory_conn is not None:
            # Reuse the single in-memory connection so tables persist.
            return self._memory_conn
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        """Creates tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_nickname TEXT NOT NULL,
                    company TEXT NOT NULL,
                    role TEXT NOT NULL,
                    round_type TEXT NOT NULL,
                    difficulty_level INTEGER DEFAULT 3,
                    status TEXT DEFAULT 'IN_PROGRESS',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    overall_score REAL DEFAULT 0.0,
                    final_verdict TEXT DEFAULT 'IN_PROGRESS',
                    condensed_summary TEXT DEFAULT ''
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_number INTEGER NOT NULL,
                    question_id TEXT,
                    question TEXT NOT NULL,
                    expected_points TEXT,
                    candidate_answer TEXT,
                    is_followup INTEGER DEFAULT 0,
                    correctness REAL DEFAULT 0.0,
                    depth REAL DEFAULT 0.0,
                    communication REAL DEFAULT 0.0,
                    overall REAL DEFAULT 0.0,
                    matched_points TEXT,
                    missed_points TEXT,
                    red_flags TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    session_id TEXT PRIMARY KEY,
                    report_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                );
            """)
            conn.commit()

    def upsert_session(
        self,
        state: InterviewState,
        user_nickname: str = "Student",
        status: str = "IN_PROGRESS",
        overall_score: float = 0.0,
        final_verdict: str = "IN_PROGRESS",
        condensed_summary: str = "",
    ) -> None:
        """Inserts or updates an interview session."""
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (
                    session_id, user_nickname, company, role, round_type,
                    difficulty_level, status, created_at, updated_at,
                    overall_score, final_verdict, condensed_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    status=excluded.status,
                    updated_at=excluded.updated_at,
                    overall_score=excluded.overall_score,
                    final_verdict=excluded.final_verdict,
                    condensed_summary=excluded.condensed_summary;
            """, (
                state.session_id,
                user_nickname,
                state.company,
                state.role,
                state.round_type,
                state.difficulty_level,
                status,
                now,
                now,
                overall_score,
                final_verdict,
                condensed_summary,
            ))
            conn.commit()

    def save_turn(self, session_id: str, turn: TurnRecord) -> None:
        """Appends a turn record into the database."""
        now = datetime.datetime.now().isoformat()
        ev = turn.evaluation
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO turns (
                    session_id, turn_number, question_id, question,
                    expected_points, candidate_answer, is_followup,
                    correctness, depth, communication, overall,
                    matched_points, missed_points, red_flags, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                turn.turn_number,
                turn.question_id,
                turn.question,
                "|".join(turn.expected_points),
                turn.candidate_answer,
                1 if turn.is_followup else 0,
                ev.correctness if ev else 0.0,
                ev.depth if ev else 0.0,
                ev.communication if ev else 0.0,
                ev.overall if ev else 0.0,
                "|".join(ev.matched_points) if ev else "",
                "|".join(ev.missed_points) if ev else "",
                "|".join(ev.red_flags) if ev else "",
                now,
            ))
            conn.commit()

    def save_report(self, session_id: str, report: SessionReport | dict[str, Any]) -> None:
        """Stores a serialized session report JSON."""
        now = datetime.datetime.now().isoformat()
        report_data = report.model_dump() if hasattr(report, "model_dump") else report
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reports (session_id, report_json, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    report_json=excluded.report_json,
                    created_at=excluded.created_at;
            """, (session_id, json.dumps(report_data), now))
            conn.commit()

    def get_user_sessions(self, user_nickname: str) -> list[dict[str, Any]]:
        """Retrieves history of past sessions for a user nickname."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions
                WHERE user_nickname = ?
                ORDER BY created_at DESC;
            """, (user_nickname,))
            return [dict(row) for row in cursor.fetchall()]

    def get_session_turns(self, session_id: str) -> list[TurnRecord]:
        """Loads all turn records for a given session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM turns
                WHERE session_id = ?
                ORDER BY turn_number ASC;
            """, (session_id,))
            rows = cursor.fetchall()

        turns: list[TurnRecord] = []
        for r in rows:
            ev = None
            if r["overall"] > 0.0 or r["correctness"] > 0.0:
                ev = EvaluationResult(
                    correctness=float(r["correctness"]),
                    depth=float(r["depth"]),
                    communication=float(r["communication"]),
                    overall=float(r["overall"]),
                    matched_points=[p for p in str(r["matched_points"]).split("|") if p],
                    missed_points=[p for p in str(r["missed_points"]).split("|") if p],
                    red_flags=[p for p in str(r["red_flags"]).split("|") if p],
                )

            turns.append(
                TurnRecord(
                    turn_number=r["turn_number"],
                    question_id=r["question_id"],
                    question=r["question"],
                    expected_points=[p for p in str(r["expected_points"]).split("|") if p],
                    candidate_answer=r["candidate_answer"] or "",
                    is_followup=bool(r["is_followup"]),
                    evaluation=ev,
                )
            )
        return turns


# ==============================================================================
# In-Memory Session Memory with Context Condensation
# ==============================================================================

class SessionMemory:
    """
    In-memory state and conversational message history for the active session,
    with automatic turn condensation when history length exceeds a threshold.
    """

    def __init__(
        self,
        session_id: str | None = None,
        company: str | None = None,
        role: str | None = None,
        round_type: str = "Technical",
        difficulty_level: int = 3,
        user_nickname: str = "Student",
        condense_threshold: int = 4,
        sqlite_store: SQLiteSessionStore | None = None,
        initial_state: InterviewState | None = None,
    ):
        if initial_state is not None:
            self.state = initial_state
            self.user_nickname = getattr(initial_state, "user_nickname", user_nickname) or user_nickname
        else:
            self.state = InterviewState(
                session_id=session_id or "default_session",
                company=company or "Zoho",
                role=role or "Software Development Engineer",
                round_type=round_type,
                difficulty_level=difficulty_level,
            )
            self.user_nickname = user_nickname

        self.condense_threshold = condense_threshold
        self.sqlite_store = sqlite_store or SQLiteSessionStore()

        self.messages: list[BaseMessage] = []
        self.condensed_summary: str = ""
        self.active_turn: TurnRecord | None = None

        # Synchronize initial session record in DB
        self.sqlite_store.upsert_session(self.state, user_nickname=self.user_nickname)

    @property
    def has_pending_question(self) -> bool:
        """True if an interview question has been asked and is awaiting candidate answer."""
        return self.active_turn is not None and not bool(self.active_turn.candidate_answer.strip())

    def get_active_turn(self) -> TurnRecord | None:
        """Returns the currently active turn."""
        return self.active_turn

    def start_new_turn(
        self,
        question: str,
        expected_points: list[str] | str = "",
        question_id: str | None = None,
        is_followup: bool = False,
        topic: str | None = None,
        round_type: str | None = None,
    ) -> TurnRecord:
        """Registers a newly asked question as the active turn."""
        turn_num = len(self.state.history) + 1
        record = TurnRecord(
            turn_number=turn_num,
            question_id=question_id,
            question=question,
            expected_points=expected_points,
            is_followup=is_followup,
            topic=topic,
            round_type=round_type or self.state.round_type,
        )
        self.active_turn = record
        if question_id:
            self.state.asked_ids.append(question_id)

        # Append to message history
        self.messages.append(AIMessage(content=f"Question {turn_num}: {question}"))

        return record

    def record_candidate_answer(self, answer: str) -> None:
        """Records candidate's answer for the active turn."""
        if self.active_turn is None:
            raise RuntimeError("No active question to answer.")
        self.active_turn.candidate_answer = answer.strip()
        self.messages.append(HumanMessage(content=answer.strip()))

    def complete_active_turn(self, evaluation: EvaluationResult) -> TurnRecord:
        """Attaches evaluation to active turn, commits to history, and persists to DB."""
        if self.active_turn is None:
            raise RuntimeError("No active turn to complete.")

        self.active_turn.evaluation = evaluation
        completed_turn = self.active_turn
        self.state.history.append(completed_turn)
        self.state.turn_count += 1
        if completed_turn.is_followup:
            self.state.followup_count += 1

        # Persist turn to SQLite
        self.sqlite_store.save_turn(self.state.session_id, completed_turn)

        # Condense older history if past threshold
        self.condense_history(threshold=self.condense_threshold)

        # Clear active turn pointer
        self.active_turn = None
        return completed_turn

    def condense_history(self, threshold: int = 4) -> None:
        """
        Condenses turns older than threshold into a concise summary block,
        protecting the LLM context window while preserving scores & core topics.
        """
        if len(self.state.history) <= threshold:
            return

        # Keep the latest 2 turns intact; condense earlier turns
        turns_to_condense = self.state.history[:-2]
        condensed_lines = []
        for t in turns_to_condense:
            score_str = f"Score: {t.evaluation.overall}/10" if t.evaluation else "Unscored"
            gap_str = f"Gaps: {', '.join(t.evaluation.missed_points[:2])}" if t.evaluation and t.evaluation.missed_points else "Clean answer"
            condensed_lines.append(
                f"- Turn {t.turn_number} [Q: {t.question[:40]}...] -> {score_str} ({gap_str})"
            )

        self.condensed_summary = "\n".join(condensed_lines)
        log.info("Condensed %d past turns into summary of %d lines", len(turns_to_condense), len(condensed_lines))

        # Update SQLite with condensed summary
        self.sqlite_store.upsert_session(
            self.state,
            user_nickname=self.user_nickname,
            condensed_summary=self.condensed_summary,
        )

    def get_context_for_prompt(self) -> dict[str, Any]:
        """Provides prompt context including condensed past summary and recent messages."""
        recent_turns = self.state.history[-2:] if len(self.state.history) > 2 else self.state.history
        return {
            "session_id": self.state.session_id,
            "company": self.state.company,
            "role": self.state.role,
            "round_type": self.state.round_type,
            "condensed_summary": self.condensed_summary,
            "recent_turns_count": len(recent_turns),
            "total_turns_completed": len(self.state.history),
            "asked_ids": self.state.asked_ids,
        }
