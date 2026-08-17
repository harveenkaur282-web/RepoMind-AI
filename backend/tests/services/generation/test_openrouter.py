from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.app.core.config import Settings
from backend.app.services.generation.base import LLMProvider, LLMProviderError
from backend.app.services.generation.factory import get_llm_provider
from backend.app.services.generation.openrouter import OpenRouterProvider


@pytest.mark.asyncio
async def test_openrouter_generate_success() -> None:
    provider = OpenRouterProvider(api_key="test_key", model="test_model")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "OpenRouter response"}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = await provider.generate(
            context="Some codebase context",
            query="Explain the code",
            system_prompt="Developer instructions",
        )

        assert response == "OpenRouter response"
        mock_post.assert_called_once()

        # Verify arguments passed to post
        args, kwargs = mock_post.call_args
        assert args[0] == "https://openrouter.ai/api/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer test_key"
        payload = kwargs["json"]
        assert payload["model"] == "test_model"
        assert payload["messages"][0] == {"role": "system", "content": "Developer instructions"}
        assert "Some codebase context" in payload["messages"][1]["content"]


@pytest.mark.asyncio
async def test_openrouter_generate_http_error() -> None:
    provider = OpenRouterProvider(api_key="test_key", model="test_model")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
        response = httpx.Response(401, request=request)
        mock_post.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=request,
            response=response,
        )

        with pytest.raises(LLMProviderError, match="HTTP error: 401"):
            await provider.generate(context="context", query="query")


@pytest.mark.asyncio
async def test_openrouter_generate_request_error() -> None:
    provider = OpenRouterProvider(api_key="test_key", model="test_model")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.RequestError("Connection timeout")

        with pytest.raises(LLMProviderError, match="communicate with OpenRouter"):
            await provider.generate(context="context", query="query")


@pytest.mark.asyncio
async def test_openrouter_generate_malformed_response() -> None:
    provider = OpenRouterProvider(api_key="test_key", model="test_model")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"bad_key": []}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(LLMProviderError, match="Malformed response format"):
            await provider.generate(context="context", query="query")


def test_openrouter_provider_conformance() -> None:
    provider: LLMProvider = OpenRouterProvider(api_key="key", model="test")
    assert provider is not None


def test_factory_get_llm_provider() -> None:
    # 1. Test Ollama selection
    settings = Settings(
        llm_provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="test-ollama",
    )
    provider = get_llm_provider(settings)
    assert provider.__class__.__name__ == "OllamaProvider"

    # 2. Test OpenRouter selection with missing key
    settings_no_key = Settings(
        llm_provider="openrouter",
        openrouter_api_key=None,
    )
    with pytest.raises(LLMProviderError, match="OpenRouter API key is not configured"):
        get_llm_provider(settings_no_key)

    # 3. Test OpenRouter selection success
    settings_success = Settings(
        llm_provider="openrouter",
        openrouter_api_key="sk-test",
        openrouter_model="test-model",
    )
    provider_or = get_llm_provider(settings_success)
    assert provider_or.__class__.__name__ == "OpenRouterProvider"
    assert provider_or.api_key == "sk-test"
    assert provider_or.model == "test-model"

    # 4. Test fallback selection to Ollama
    settings_fallback = Settings(
        llm_provider="unsupported-name",
        ollama_url="http://localhost:11434",
        ollama_model="test-ollama",
    )
    provider_fallback = get_llm_provider(settings_fallback)
    assert provider_fallback.__class__.__name__ == "OllamaProvider"
