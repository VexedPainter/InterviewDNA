"""
src/rag/retriever.py — Semantic retriever with metadata filtering, graceful fallback,
and recency-weighted re-ranking for interview questions and historical feedback.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from config import settings
from src.schemas.rag import FeedbackResult, QuestionResult, RetrievalResponse

log = logging.getLogger(__name__)

# Constants for recency normalization (2016 to 2025 archive)
MIN_ARCHIVE_YEAR = 2016
MAX_ARCHIVE_YEAR = 2025


class InterviewRetriever:
    """
    RAG retriever interfacing with the two ChromaDB collections:
    'questions' and 'feedback'.
    """

    def __init__(
        self,
        persist_dir: str | None = None,
        embedding_model: str | None = None,
    ):
        self.persist_dir = persist_dir or str(settings.chroma_persist_path)
        self.embedding_model = embedding_model or settings.embedding_model
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.q_col = self.client.get_or_create_collection(
            name="questions",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        self.fb_col = self.client.get_or_create_collection(
            name="feedback",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def _build_where_clause(
        self,
        company: str,
        role: str | None = None,
        round_type: str | None = None,
        topic: str | None = None,
    ) -> dict[str, Any] | None:
        """Constructs a ChromaDB where filter adhering to single-key or $and requirements."""
        clauses = [{"company": {"$eq": company}}]
        if role:
            clauses.append({"role": {"$eq": role}})
        if round_type:
            clauses.append({"round_type": {"$eq": round_type}})
        if topic:
            clauses.append({"topic": {"$eq": topic}})

        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    def get_questions(
        self,
        company: str,
        role: str,
        round_type: str | None = None,
        topic: str | None = None,
        difficulty_range: tuple[int, int] | None = None,
        exclude_ids: list[str] | None = None,
        query: str | None = None,
        k: int = 5,
    ) -> RetrievalResponse:
        """
        Retrieves relevant interview questions with metadata filtering,
        deduplication against exclude_ids, and graceful fallback.

        Fallback Levels:
        1. 'company_role': company + role (plus optional round_type, topic)
        2. 'company_only': company only (broadens if insufficient results)
        3. 'unfiltered': system-wide fallback
        """
        exclude_set = set(exclude_ids or [])
        query_text = query or f"{company} {role} {round_type or ''} {topic or ''} technical interview question".strip()

        # Attempt 1: company + role
        where_filter = self._build_where_clause(
            company=company, role=role, round_type=round_type, topic=topic
        )
        questions, fallback_level = self._execute_question_query(
            query_text=query_text,
            where=where_filter,
            difficulty_range=difficulty_range,
            exclude_set=exclude_set,
            k=k,
            level="company_role",
        )

        # Attempt 2: fallback to company-only if fewer than k results
        if len(questions) < k:
            log.warning(
                "Fallback triggered for questions: company='%s', role='%s' produced %d < %d results. Widening to company-only.",
                company,
                role,
                len(questions),
                k,
            )
            where_company_only = self._build_where_clause(
                company=company, role=None, round_type=round_type, topic=topic
            )
            wider_questions, wider_level = self._execute_question_query(
                query_text=query_text,
                where=where_company_only,
                difficulty_range=difficulty_range,
                exclude_set=exclude_set,
                k=k,
                level="company_only",
            )
            if len(wider_questions) >= len(questions):
                questions = wider_questions
                fallback_level = wider_level

        # Attempt 3: system-wide unfiltered fallback (rare safety net)
        if len(questions) < k:
            log.warning(
                "Fallback level 2 triggered: company-only produced %d < %d results. Falling back to unfiltered.",
                len(questions),
                k,
            )
            unfiltered_questions, unfilt_level = self._execute_question_query(
                query_text=query_text,
                where=None,
                difficulty_range=difficulty_range,
                exclude_set=exclude_set,
                k=k,
                level="unfiltered",
            )
            if len(unfiltered_questions) >= len(questions):
                questions = unfiltered_questions
                fallback_level = unfilt_level

        # Graceful degradation: Fall back to direct CSV archive if ChromaDB is empty or failed
        if not questions:
            questions = self._csv_question_fallback(
                company=company, role=role, round_type=round_type, exclude_set=exclude_set, k=k
            )
            if questions:
                fallback_level = "csv_archive_direct"

        return RetrievalResponse(
            items=questions[:k],
            fallback_level=fallback_level,
            query=query_text,
            total_found=len(questions),
        )

    def _execute_question_query(
        self,
        query_text: str,
        where: dict[str, Any] | None,
        difficulty_range: tuple[int, int] | None,
        exclude_set: set[str],
        k: int,
        level: str,
    ) -> tuple[list[QuestionResult], str]:
        """Runs Chroma query for questions and parses metadata and expected points."""
        fetch_limit = max(k * 4, 25)
        try:
            results = self.q_col.query(
                query_texts=[query_text],
                n_results=fetch_limit,
                where=where,
            )
        except Exception as e:
            log.error("Chroma query error at level %s: %s", level, e)
            return [], level

        items: list[QuestionResult] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return [], level

        ids = results["ids"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else []
        docs = results["documents"][0] if results.get("documents") else []
        distances = results["distances"][0] if results.get("distances") else [0.5] * len(ids)

        for rid, meta, doc, dist in zip(ids, metas, docs, distances):
            if rid in exclude_set:
                continue

            diff = int(meta.get("difficulty", 3))
            if difficulty_range:
                min_d, max_d = difficulty_range
                if not (min_d <= diff <= max_d):
                    continue

            # Extract question and expected points from document text
            question_text = ""
            expected_pts: list[str] = []
            if "Interview Question:" in doc:
                parts = doc.split("Interview Question:")
                if len(parts) > 1:
                    subparts = parts[1].split("Expected Points in Answer:")
                    question_text = subparts[0].strip()
                    if len(subparts) > 1:
                        for line in subparts[1].strip().split("\n"):
                            line = line.strip().lstrip("-").strip()
                            if line:
                                expected_pts.append(line)

            items.append(
                QuestionResult(
                    record_id=rid,
                    question=question_text or doc,
                    expected_points=expected_pts,
                    company=meta.get("company", ""),
                    role=meta.get("role", ""),
                    round_type=meta.get("round_type", ""),
                    topic=meta.get("topic", ""),
                    difficulty=diff,
                    year=int(meta.get("year", 2020)),
                    similarity=round(1.0 - dist, 4),
                )
            )

        return items, level

    def get_feedback(
        self,
        company: str,
        role: str,
        query: str,
        k: int = 5,
        base_weight: float = 0.7,
        recency_weight: float = 0.3,
    ) -> RetrievalResponse:
        """
        Retrieves historical feedback records with RECENCY-WEIGHTED re-ranking.

        Formula:
            recency_factor = (year - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)  [0.0 to 1.0]
            final_score = similarity * (base_weight + recency_weight * recency_factor)

        Graceful fallback:
            1. 'company_role' filter
            2. 'company_only' filter if fewer than k matches
        """
        where_filter = self._build_where_clause(company=company, role=role)
        feedback_items, fallback_level = self._execute_feedback_query(
            query=query,
            where=where_filter,
            k=k,
            level="company_role",
            base_weight=base_weight,
            recency_weight=recency_weight,
        )

        if len(feedback_items) < k:
            log.warning(
                "Feedback fallback triggered: company='%s', role='%s' produced %d < %d results. Widening to company-only.",
                company,
                role,
                len(feedback_items),
                k,
            )
            where_company_only = self._build_where_clause(company=company, role=None)
            wider_items, wider_level = self._execute_feedback_query(
                query=query,
                where=where_company_only,
                k=k,
                level="company_only",
                base_weight=base_weight,
                recency_weight=recency_weight,
            )
            if len(wider_items) >= len(feedback_items):
                feedback_items = wider_items
                fallback_level = wider_level

        # Re-sort strictly by final_score descending
        feedback_items.sort(key=lambda x: x.final_score, reverse=True)

        # Graceful degradation: Fall back to direct CSV archive if ChromaDB is empty or failed
        if not feedback_items:
            feedback_items = self._csv_feedback_fallback(company=company, role=role, k=k)
            if feedback_items:
                fallback_level = "csv_archive_direct"

        return RetrievalResponse(
            items=feedback_items[:k],
            fallback_level=fallback_level,
            query=query,
            total_found=len(feedback_items),
        )

    def _execute_feedback_query(
        self,
        query: str,
        where: dict[str, Any] | None,
        k: int,
        level: str,
        base_weight: float,
        recency_weight: float,
    ) -> tuple[list[FeedbackResult], str]:
        """Runs Chroma query for feedback records and computes recency-weighted scores."""
        fetch_limit = max(k * 4, 30)
        try:
            results = self.fb_col.query(
                query_texts=[query],
                n_results=fetch_limit,
                where=where,
            )
        except Exception as e:
            log.error("Feedback query failed at level %s: %s", level, e)
            return [], level

        items: list[FeedbackResult] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return [], level

        ids = results["ids"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else []
        docs = results["documents"][0] if results.get("documents") else []
        distances = results["distances"][0] if results.get("distances") else [0.5] * len(ids)

        for rid, meta, doc, dist in zip(ids, metas, docs, distances):
            year = int(meta.get("year", 2020))
            raw_similarity = max(0.0, 1.0 - dist)

            # Recency factor from 0.0 to 1.0
            if MAX_ARCHIVE_YEAR > MIN_ARCHIVE_YEAR:
                recency_factor = max(
                    0.0, min(1.0, (year - MIN_ARCHIVE_YEAR) / (MAX_ARCHIVE_YEAR - MIN_ARCHIVE_YEAR))
                )
            else:
                recency_factor = 1.0

            # Re-ranking formula
            final_score = raw_similarity * (base_weight + recency_weight * recency_factor)

            # Extract text sections
            candidate_summary = ""
            feedback_text = ""
            if "Candidate Answer Summary:" in doc:
                parts = doc.split("Candidate Answer Summary:")
                if len(parts) > 1:
                    subparts = parts[1].split("Interviewer Feedback:")
                    candidate_summary = subparts[0].strip()
                    if len(subparts) > 1:
                        feedback_text = subparts[1].strip()

            raw_tags = str(meta.get("feedback_tags", ""))
            tags = [t.strip() for t in raw_tags.split("|") if t.strip()]

            items.append(
                FeedbackResult(
                    record_id=rid,
                    feedback_text=feedback_text or doc,
                    candidate_answer_summary=candidate_summary,
                    company=meta.get("company", ""),
                    role=meta.get("role", ""),
                    round_type=meta.get("round_type", ""),
                    topic=meta.get("topic", ""),
                    year=year,
                    feedback_tags=tags,
                    score_given=float(meta.get("score_given", 5.0)),
                    outcome=str(meta.get("outcome", "Unknown")),
                    raw_similarity=round(raw_similarity, 4),
                    recency_factor=round(recency_factor, 4),
                    final_score=round(final_score, 4),
                )
            )

        return items, level

    def _csv_question_fallback(
        self,
        company: str,
        role: str | None,
        round_type: str | None,
        exclude_set: set[str],
        k: int,
    ) -> list[QuestionResult]:
        """Directly parses archive CSV when ChromaDB returns insufficient results or is offline."""
        csv_path = Path(settings.archive_csv_path)
        if not csv_path.exists():
            return []
        import csv
        results: list[QuestionResult] = []
        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rid = row.get("record_id", "")
                    if rid in exclude_set:
                        continue
                    if company and row.get("company", "").lower() != company.lower():
                        continue
                    if round_type and row.get("round_type", "").lower() != round_type.lower():
                        continue
                    exp_pts = [p.strip() for p in row.get("expected_points", "").split("|") if p.strip()]
                    results.append(
                        QuestionResult(
                            record_id=rid,
                            question=row.get("question", ""),
                            expected_points=exp_pts,
                            company=row.get("company", company),
                            role=row.get("role", role or ""),
                            round_type=row.get("round_type", "Technical"),
                            topic=row.get("topic", "General"),
                            difficulty=int(row.get("difficulty", 3)),
                            year=int(row.get("year", 2024)),
                            similarity=0.85,
                        )
                    )
                    if len(results) >= k:
                        break
        except Exception as exc:
            log.warning("CSV question fallback failed: %s", exc)
        return results

    def _csv_feedback_fallback(
        self,
        company: str,
        role: str | None,
        k: int,
    ) -> list[FeedbackResult]:
        """Directly parses archive CSV for feedback when ChromaDB is offline."""
        csv_path = Path(settings.archive_csv_path)
        if not csv_path.exists():
            return []
        import csv
        results: list[FeedbackResult] = []
        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rid = row.get("record_id", "")
                    if company and row.get("company", "").lower() != company.lower():
                        continue
                    tags = [t.strip() for t in row.get("feedback_tags", "").split("|") if t.strip()]
                    yr = int(row.get("year", 2024))
                    results.append(
                        FeedbackResult(
                            record_id=rid,
                            feedback_text=row.get("feedback_text", ""),
                            candidate_answer_summary=row.get("candidate_answer_summary", ""),
                            company=row.get("company", company),
                            role=row.get("role", role or ""),
                            round_type=row.get("round_type", "Technical"),
                            topic=row.get("topic", "General"),
                            year=yr,
                            feedback_tags=tags,
                            score_given=float(row.get("score_given", 5.0)),
                            outcome=row.get("outcome", "Unknown"),
                            raw_similarity=0.85,
                            recency_factor=0.9,
                            final_score=0.85,
                        )
                    )
                    if len(results) >= k:
                        break
        except Exception as exc:
            log.warning("CSV feedback fallback failed: %s", exc)
        return results
