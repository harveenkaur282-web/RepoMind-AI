from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.app.core.config import Settings
from backend.app.services.generation.base import LLMProvider, LLMProviderError
from backend.app.services.generation.factory import get_llm_provider
from backend.app.services.generation.groq import GroqProvider


@pytest.mark.asyncio
async def test_groq_generate_success() -> None:
    provider = GroqProvider(api_key="groq_key", model="llama-3.1-70b-versatile")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "Groq response content"}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = await provider.generate(
            context="Groq context info",
            query="Analyze this codebase",
            system_prompt="Coding instructions",
        )

        assert response == "Groq response content"
        mock_post.assert_called_once()

        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.groq.com/openai/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer groq_key"
        payload = kwargs["json"]
        assert payload["model"] == "llama-3.1-70b-versatile"
        assert payload["messages"][0] == {"role": "system", "content": "Coding instructions"}


@pytest.mark.asyncio
async def test_groq_generate_http_error() -> None:
    provider = GroqProvider(api_key="groq_key", model="llama-3.1-70b-versatile")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        request = httpx.Request(
            "POST",
            "https://api.groq.com/openai/v1/chat/completions",
        )
        response = httpx.Response(400, request=request)
        mock_post.side_effect = httpx.HTTPStatusError(
            "Bad Request",
            request=request,
            response=response,
        )

        with pytest.raises(LLMProviderError, match="HTTP error: 400"):
            await provider.generate(context="context", query="query")


@pytest.mark.asyncio
async def test_groq_generate_request_error() -> None:
    provider = GroqProvider(api_key="groq_key", model="llama-3.1-70b-versatile")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.RequestError("Host unreachable")

        with pytest.raises(LLMProviderError, match="communicate with Groq"):
            await provider.generate(context="context", query="query")


@pytest.mark.asyncio
async def test_groq_generate_malformed_response() -> None:
    provider = GroqProvider(api_key="groq_key", model="llama-3.1-70b-versatile")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"bad_key": None}]}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(LLMProviderError, match="Malformed response format"):
            await provider.generate(context="context", query="query")


def test_groq_provider_conformance() -> None:
    provider: LLMProvider = GroqProvider(api_key="key", model="test")
    assert provider is not None


def test_factory_get_groq_provider() -> None:
    # 1. Test Groq selection with missing key
    settings_no_key = Settings(
        llm_provider="groq",
        groq_api_key=None,
    )
    with pytest.raises(LLMProviderError, match="Groq API key is not configured"):
        get_llm_provider(settings_no_key)

    # 2. Test Groq selection success
    settings_success = Settings(
        llm_provider="groq",
        groq_api_key="groq-sk",
        groq_model="llama3-8b-8192",
    )
    provider_grq = get_llm_provider(settings_success)
    assert provider_grq.__class__.__name__ == "GroqProvider"
    assert provider_grq.api_key == "groq-sk"
    assert provider_grq.model == "llama3-8b-8192"
