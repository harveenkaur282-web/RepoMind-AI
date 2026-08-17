from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.services.generation.base import LLMProvider, LLMProviderError
from backend.app.services.generation.gemini import GeminiProvider
from backend.app.services.generation.groq import GroqProvider
from backend.app.services.generation.ollama import OllamaProvider
from backend.app.services.generation.openrouter import OpenRouterProvider


def validate_llm_settings(settings: Settings) -> None:
    """Validate that the required settings and API keys exist for the selected provider."""
    provider_name = settings.llm_provider.lower()
    if provider_name == "openrouter":
        if not settings.openrouter_api_key:
            raise LLMProviderError(
                "OpenRouter API key is required when openrouter is the selected provider."
            )
    elif provider_name == "gemini":
        if not settings.gemini_api_key:
            raise LLMProviderError(
                "Gemini API key is required when gemini is the selected provider."
            )
    elif provider_name == "groq":
        if not settings.groq_api_key:
            raise LLMProviderError("Groq API key is required when groq is the selected provider.")
    elif provider_name == "ollama":
        pass
    else:
        # Fallback to Ollama is allowed for backward compatibility
        pass


def get_llm_provider(settings: Settings) -> LLMProvider:
    """Return the configured LLMProvider instance based on validated application settings."""
    validate_llm_settings(settings)

    provider_name = settings.llm_provider.lower()
    if provider_name == "openrouter":
        return OpenRouterProvider(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
        )
    elif provider_name == "gemini":
        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
    elif provider_name == "groq":
        return GroqProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
        )
    else:
        # Default fallback to OllamaProvider to preserve compatibility
        # with existing configurations and test overrides
        return OllamaProvider(
            base_url=settings.ollama_url,
            model=settings.ollama_model,
        )
