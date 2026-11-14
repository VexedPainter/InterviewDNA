"""
src/llm/provider.py — Factory abstraction for LangChain Chat Models (Gemini & Ollama).

Features:
- Dynamically selects provider from config / .env (LLM_PROVIDER: "gemini" | "ollama").
- Parametric temperature, timeout, and exponential retry backoff.
- Clear, actionable error messages if keys or endpoints are misconfigured.
"""

from __future__ import annotations

import logging

from langchain_core.language_models.chat_models import BaseChatModel

from config import settings

log = logging.getLogger(__name__)


class LLMConfigurationError(Exception):
    """Raised when an LLM provider cannot be configured due to missing credentials or endpoints."""


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.2,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> BaseChatModel:
    """
    Factory function returning a configured LangChain ChatModel with retries and timeout.

    Args:
        provider: "gemini" or "ollama". Defaults to settings.llm_provider.
        model: Specific model name (e.g. "gemini-1.5-flash", "llama3.2").
        temperature: Sampling temperature (0.0 for strict evaluation, 0.7 for conversational).
        timeout: Request timeout in seconds.
        max_retries: Number of retries with backoff upon rate limit or transient failure.

    Returns:
        BaseChatModel instance.

    Raises:
        LLMConfigurationError: If required API keys or configurations are missing.
        ValueError: If an unsupported provider is requested.
    """
    selected_provider = (provider or settings.llm_provider).lower()

    if selected_provider == "gemini":
        api_key = settings.google_api_key
        if not api_key or api_key == "your_google_api_key_here":
            raise LLMConfigurationError(
                "Google Gemini selected as LLM provider, but GOOGLE_API_KEY is not set or is a placeholder in .env. "
                "Please configure a valid key in .env or switch LLM_PROVIDER=ollama."
            )

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            model_name = model or settings.gemini_model
            log.info("Initializing ChatGoogleGenerativeAI: model=%s, temp=%.2f", model_name, temperature)

            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=temperature,
                timeout=timeout,
                max_retries=max_retries,
            )
        except ImportError as e:
            raise LLMConfigurationError(
                f"langchain-google-genai package is not installed: {e}. Run `pip install langchain-google-genai`."
            )

    elif selected_provider == "ollama":
        base_url = settings.ollama_base_url
        model_name = model or settings.ollama_model

        if not base_url:
            raise LLMConfigurationError(
                "Ollama selected as LLM provider, but OLLAMA_BASE_URL is missing. Please set it in .env (e.g. http://localhost:11434)."
            )

        try:
            from langchain_ollama import ChatOllama

            log.info("Initializing ChatOllama: model=%s at %s, temp=%.2f", model_name, base_url, temperature)

            return ChatOllama(
                model=model_name,
                base_url=base_url,
                temperature=temperature,
                timeout=timeout,
                num_predict=1024,
            )
        except ImportError as e:
            raise LLMConfigurationError(
                f"langchain-ollama package is not installed: {e}. Run `pip install langchain-ollama`."
            )

    else:
        raise ValueError(
            f"Unsupported LLM provider '{selected_provider}'. Allowed providers are: 'gemini', 'ollama'."
        )
