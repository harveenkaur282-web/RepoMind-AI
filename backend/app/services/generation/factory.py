from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.services.generation.base import LLMProvider, LLMProviderError
from backend.app.services.generation.ollama import OllamaProvider
from backend.app.services.generation.openrouter import OpenRouterProvider


def get_llm_provider(settings: Settings) -> LLMProvider:
    """Return the configured LLMProvider instance based on application settings."""
    provider_name = settings.llm_provider.lower()
    if provider_name == "openrouter":
        if not settings.openrouter_api_key:
            raise LLMProviderError("OpenRouter API key is not configured.")
        return OpenRouterProvider(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
        )
    else:
        # Default fallback to OllamaProvider to preserve compatibility
        # with existing configurations and test overrides
        return OllamaProvider(
            base_url=settings.ollama_url,
            model=settings.ollama_model,
        )
