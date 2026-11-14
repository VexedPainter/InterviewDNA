"""
src/rag/ingest.py — Idempotent ingestion pipeline for InterviewDNA into ChromaDB.

Creates and populates two Chroma collections:
1. 'questions': Document = question + expected points. Metadata = record_id, company, role, round_type, topic, difficulty, year.
2. 'feedback': Document = feedback text + candidate answer summary. Metadata = record_id, company, role, round_type, topic, year, feedback_tags, score_given, outcome.

Usage:
    python -m src.rag.ingest [--reset]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Fix Windows console UTF-8 output encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import chromadb
import pandas as pd
from chromadb.utils import embedding_functions
from tqdm import tqdm

from config import settings

log = logging.getLogger(__name__)


def get_embedding_function():
    """Returns local offline SentenceTransformer embedding function."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=settings.embedding_model
    )


def get_chroma_client() -> chromadb.PersistentClient:
    """Returns a persistent ChromaDB client pointing to configured directory."""
    persist_dir = str(settings.chroma_persist_path)
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=persist_dir)


def prepare_question_doc(row: pd.Series) -> str:
    """Builds the textual content for the question collection."""
    pts = str(row["expected_points"]).split("|")
    pts_formatted = "\n".join(f"- {p.strip()}" for p in pts if p.strip())
    return (
        f"Company: {row['company']} | Role: {row['role']} | Topic: {row['topic']} | Round: {row['round_type']}\n"
        f"Difficulty: {row['difficulty']}/5 | Year: {row['year']}\n\n"
        f"Interview Question:\n{row['question']}\n\n"
        f"Expected Points in Answer:\n{pts_formatted}"
    )


def prepare_feedback_doc(row: pd.Series) -> str:
    """Builds the textual content for the feedback collection."""
    tags = str(row["feedback_tags"]).replace("|", ", ")
    return (
        f"Company: {row['company']} | Role: {row['role']} | Topic: {row['topic']} | Round: {row['round_type']}\n"
        f"Outcome: {row['outcome']} | Score: {row['score_given']}/10 | Year: {row['year']}\n"
        f"Tags: {tags}\n\n"
        f"Candidate Answer Summary:\n{row['candidate_answer_summary']}\n\n"
        f"Interviewer Feedback:\n{row['feedback_text']}"
    )


def ingest_archive(
    csv_path: str | None = None,
    reset: bool = False,
    batch_size: int = 100,
) -> None:
    """
    Ingests interview_archive.csv into ChromaDB collections idempotently.

    Args:
        csv_path: Path to interview_archive.csv (defaults to config setting).
        reset: If True, drops existing collections before ingesting.
        batch_size: Number of records to add per batch.
    """
    path = Path(csv_path or settings.archive_csv_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Archive CSV not found at: {path}")

    log.info("Loading archive from %s", path)
    df = pd.read_csv(path)
    total_rows = len(df)
    log.info("Loaded %d rows for ingestion", total_rows)

    client = get_chroma_client()
    embedding_fn = get_embedding_function()

    # Reset collections if requested
    if reset:
        log.warning("Reset requested: deleting existing 'questions' and 'feedback' collections")
        try:
            client.delete_collection("questions")
        except Exception:
            pass
        try:
            client.delete_collection("feedback")
        except Exception:
            pass

    q_col = client.get_or_create_collection(
        name="questions",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )
    fb_col = client.get_or_create_collection(
        name="feedback",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # Idempotence: Find existing IDs in the collections
    existing_q_ids = set()
    existing_fb_ids = set()
    if not reset:
        all_ids = [str(r) for r in df["record_id"].tolist()]
        # Check in chunks to avoid memory/query limits
        for i in range(0, len(all_ids), 1000):
            chunk = all_ids[i : i + 1000]
            res_q = q_col.get(ids=chunk, include=[])
            existing_q_ids.update(res_q["ids"])
            res_fb = fb_col.get(ids=chunk, include=[])
            existing_fb_ids.update(res_fb["ids"])
        log.info(
            "Found %d existing questions and %d existing feedback records",
            len(existing_q_ids),
            len(existing_fb_ids),
        )

    # Filter rows that need ingestion
    df_q_new = df[~df["record_id"].astype(str).isin(existing_q_ids)]
    df_fb_new = df[~df["record_id"].astype(str).isin(existing_fb_ids)]

    log.info(
        "Ingesting %d new questions and %d new feedback records",
        len(df_q_new),
        len(df_fb_new),
    )

    # 1. Ingest questions
    if not df_q_new.empty:
        log.info("Ingesting 'questions' collection...")
        for start in tqdm(range(0, len(df_q_new), batch_size), desc="Questions"):
            batch = df_q_new.iloc[start : start + batch_size]
            ids = [str(r["record_id"]) for _, r in batch.iterrows()]
            docs = [prepare_question_doc(r) for _, r in batch.iterrows()]
            metadatas = [
                {
                    "record_id": str(r["record_id"]),
                    "company": str(r["company"]),
                    "role": str(r["role"]),
                    "round_type": str(r["round_type"]),
                    "topic": str(r["topic"]),
                    "difficulty": int(r["difficulty"]),
                    "year": int(r["year"]),
                }
                for _, r in batch.iterrows()
            ]
            q_col.add(ids=ids, documents=docs, metadatas=metadatas)

    # 2. Ingest feedback
    if not df_fb_new.empty:
        log.info("Ingesting 'feedback' collection...")
        for start in tqdm(range(0, len(df_fb_new), batch_size), desc="Feedback"):
            batch = df_fb_new.iloc[start : start + batch_size]
            ids = [str(r["record_id"]) for _, r in batch.iterrows()]
            docs = [prepare_feedback_doc(r) for _, r in batch.iterrows()]
            metadatas = [
                {
                    "record_id": str(r["record_id"]),
                    "company": str(r["company"]),
                    "role": str(r["role"]),
                    "round_type": str(r["round_type"]),
                    "topic": str(r["topic"]),
                    "year": int(r["year"]),
                    "feedback_tags": str(r["feedback_tags"]),
                    "score_given": float(r["score_given"]),
                    "outcome": str(r["outcome"]),
                }
                for _, r in batch.iterrows()
            ]
            fb_col.add(ids=ids, documents=docs, metadatas=metadatas)

    log.info(
        "Ingestion complete. Total items in DB: questions=%d, feedback=%d",
        q_col.count(),
        fb_col.count(),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest InterviewDNA archive into ChromaDB")
    parser.add_argument("--reset", action="store_true", help="Reset collections before ingesting")
    parser.add_argument("--csv", type=str, default=None, help="Path to custom CSV file")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
    )
    ingest_archive(csv_path=args.csv, reset=args.reset)
