"""
config.py — Single source of truth for all application settings.

Loads from .env (via pydantic-settings). Import `settings` everywhere;
never read os.environ directly in application code.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All InterviewDNA configuration, sourced from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM Provider ──────────────────────────────────────────────────────────
    llm_provider: str = Field(default="gemini", description="'gemini' or 'ollama'")
    google_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-1.5-flash")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.2")

    # ── Embeddings ────────────────────────────────────────────────────────────
    embedding_model: str = Field(default="all-MiniLM-L6-v2")

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    chroma_persist_dir: str = Field(default="./chroma_db")
    chroma_collection_name: str = Field(default="interview_archive")

    # ── SQLite ────────────────────────────────────────────────────────────────
    sqlite_db_path: str = Field(default="./data/sessions.db")

    # ── Data Paths ────────────────────────────────────────────────────────────
    archive_csv_path: str = Field(default="./data/interview_archive.csv")

    # ── App Behaviour ─────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    max_retrieved_docs: int = Field(default=5, ge=1, le=20)
    interview_max_turns: int = Field(default=10, ge=1, le=30)

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = {"gemini", "ollama"}
        if v.lower() not in allowed:
            raise ValueError(f"llm_provider must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @property
    def chroma_persist_path(self) -> Path:
        return Path(self.chroma_persist_dir).resolve()

    @property
    def archive_csv(self) -> Path:
        return Path(self.archive_csv_path).resolve()

    @property
    def sqlite_path(self) -> Path:
        return Path(self.sqlite_db_path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance (cached after first call)."""
    return Settings()


def configure_logging(settings: Settings | None = None) -> None:
    """Configure root logger based on settings."""
    cfg = settings or get_settings()
    logging.basicConfig(
        level=getattr(logging, cfg.log_level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# Module-level singleton for convenience
settings = get_settings()
