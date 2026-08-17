from __future__ import annotations

import pytest

from backend.app.core.config import Settings
from backend.app.services.generation.base import LLMProviderError
from backend.app.services.generation.factory import get_llm_provider, validate_llm_settings


def test_validate_llm_settings_ollama() -> None:
    settings = Settings(
        llm_provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="qwen2.5-coder:7b",
    )
    # Should not raise any error
    validate_llm_settings(settings)
    provider = get_llm_provider(settings)
    assert provider.__class__.__name__ == "OllamaProvider"


def test_validate_llm_settings_openrouter_missing_key() -> None:
    settings = Settings(
        llm_provider="openrouter",
        openrouter_api_key=None,
    )
    with pytest.raises(LLMProviderError, match="OpenRouter API key is required"):
        validate_llm_settings(settings)


def test_validate_llm_settings_openrouter_success() -> None:
    settings = Settings(
        llm_provider="openrouter",
        openrouter_api_key="mock_openrouter_key",
        openrouter_model="meta-llama/llama-3-8b-instruct:free",
    )
    validate_llm_settings(settings)
    provider = get_llm_provider(settings)
    assert provider.__class__.__name__ == "OpenRouterProvider"
    assert provider.api_key == "mock_openrouter_key"
    assert provider.model == "meta-llama/llama-3-8b-instruct:free"


def test_validate_llm_settings_gemini_missing_key() -> None:
    settings = Settings(
        llm_provider="gemini",
        gemini_api_key=None,
    )
    with pytest.raises(LLMProviderError, match="Gemini API key is required"):
        validate_llm_settings(settings)


def test_validate_llm_settings_gemini_success() -> None:
    settings = Settings(
        llm_provider="gemini",
        gemini_api_key="mock_gemini_key",
        gemini_model="gemini-1.5-flash",
    )
    validate_llm_settings(settings)
    provider = get_llm_provider(settings)
    assert provider.__class__.__name__ == "GeminiProvider"
    assert provider.api_key == "mock_gemini_key"
    assert provider.model == "gemini-1.5-flash"


def test_validate_llm_settings_groq_missing_key() -> None:
    settings = Settings(
        llm_provider="groq",
        groq_api_key=None,
    )
    with pytest.raises(LLMProviderError, match="Groq API key is required"):
        validate_llm_settings(settings)


def test_validate_llm_settings_groq_success() -> None:
    settings = Settings(
        llm_provider="groq",
        groq_api_key="mock_groq_key",
        groq_model="llama-3.1-70b-versatile",
    )
    validate_llm_settings(settings)
    provider = get_llm_provider(settings)
    assert provider.__class__.__name__ == "GroqProvider"
    assert provider.api_key == "mock_groq_key"
    assert provider.model == "llama-3.1-70b-versatile"
