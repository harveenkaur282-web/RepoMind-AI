from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.app.core.config import Settings
from backend.app.services.generation.base import LLMProvider, LLMProviderError
from backend.app.services.generation.factory import get_llm_provider
from backend.app.services.generation.gemini import GeminiProvider


@pytest.mark.asyncio
async def test_gemini_generate_success() -> None:
    provider = GeminiProvider(api_key="gemini_key", model="gemini-1.5-flash")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "Gemini response text"}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = await provider.generate(
            context="Gemini context info",
            query="Analyze this codebase",
            system_prompt="Coding instructions",
        )

        assert response == "Gemini response text"
        mock_post.assert_called_once()

        args, kwargs = mock_post.call_args
        assert args[0] == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer gemini_key"
        payload = kwargs["json"]
        assert payload["model"] == "gemini-1.5-flash"
        assert payload["messages"][0] == {"role": "system", "content": "Coding instructions"}


@pytest.mark.asyncio
async def test_gemini_generate_http_error() -> None:
    provider = GeminiProvider(api_key="gemini_key", model="gemini-1.5-flash")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        request = httpx.Request(
            "POST",
            "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        )
        response = httpx.Response(403, request=request)
        mock_post.side_effect = httpx.HTTPStatusError(
            "Forbidden",
            request=request,
            response=response,
        )

        with pytest.raises(LLMProviderError, match="HTTP error: 403"):
            await provider.generate(context="context", query="query")


@pytest.mark.asyncio
async def test_gemini_generate_request_error() -> None:
    provider = GeminiProvider(api_key="gemini_key", model="gemini-1.5-flash")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.RequestError("Network dropped")

        with pytest.raises(LLMProviderError, match="communicate with Gemini"):
            await provider.generate(context="context", query="query")


@pytest.mark.asyncio
async def test_gemini_generate_malformed_response() -> None:
    provider = GeminiProvider(api_key="gemini_key", model="gemini-1.5-flash")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": []}  # empty list causes IndexError

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(LLMProviderError, match="Malformed response format"):
            await provider.generate(context="context", query="query")


def test_gemini_provider_conformance() -> None:
    provider: LLMProvider = GeminiProvider(api_key="key", model="test")
    assert provider is not None


def test_factory_get_gemini_provider() -> None:
    # 1. Test Gemini selection with missing key
    settings_no_key = Settings(
        llm_provider="gemini",
        gemini_api_key=None,
    )
    with pytest.raises(LLMProviderError, match="Gemini API key is not configured"):
        get_llm_provider(settings_no_key)

    # 2. Test Gemini selection success
    settings_success = Settings(
        llm_provider="gemini",
        gemini_api_key="gemini-sk",
        gemini_model="gemini-1.5-pro",
    )
    provider_gem = get_llm_provider(settings_success)
    assert provider_gem.__class__.__name__ == "GeminiProvider"
    assert provider_gem.api_key == "gemini-sk"
    assert provider_gem.model == "gemini-1.5-pro"
