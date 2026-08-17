from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.app.core.config import get_settings
from backend.app.services.generation.base import LLMProvider, LLMProviderError
from backend.app.services.generation.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_ollama_generate_success() -> None:
    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen2.5-coder:7b")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {"role": "assistant", "content": "This is the generated response content."}
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = await provider.generate(
            context="Some test context info",
            query="Tell me about context?",
            system_prompt="Custom system prompt",
        )

        assert response == "This is the generated response content."
        mock_post.assert_called_once()

        # Verify arguments passed to post
        args, kwargs = mock_post.call_args
        assert args[0] == "http://localhost:11434/api/chat"
        payload = kwargs["json"]
        assert payload["model"] == "qwen2.5-coder:7b"
        assert payload["messages"][0] == {"role": "system", "content": "Custom system prompt"}
        assert "Some test context info" in payload["messages"][1]["content"]
        assert "Tell me about context?" in payload["messages"][1]["content"]


@pytest.mark.asyncio
async def test_ollama_generate_http_error() -> None:
    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen2.5-coder:7b")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        request = httpx.Request("POST", "http://localhost:11434/api/chat")
        response = httpx.Response(500, request=request)
        mock_post.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=request,
            response=response,
        )

        with pytest.raises(LLMProviderError, match="HTTP error: 500"):
            await provider.generate(context="context", query="query")


@pytest.mark.asyncio
async def test_ollama_generate_request_error() -> None:
    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen2.5-coder:7b")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        request = httpx.Request("POST", "http://localhost:11434/api/chat")
        mock_post.side_effect = httpx.RequestError("Connection refused", request=request)

        with pytest.raises(LLMProviderError, match="Failed to communicate"):
            await provider.generate(context="context", query="query")


def test_ollama_settings_default() -> None:
    settings = get_settings()
    assert settings.ollama_url == "http://localhost:11434"
    assert settings.ollama_model == "qwen2.5-coder:7b"


@pytest.mark.asyncio
async def test_ollama_generate_malformed_response() -> None:
    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen2.5-coder:7b")

    mock_response = MagicMock()
    mock_response.status_code = 200
    # Response JSON missing the "message" key
    mock_response.json.return_value = {"invalid_key": "some value"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(LLMProviderError, match="Malformed response format"):
            await provider.generate(context="context", query="query")


def test_ollama_provider_conforms_to_protocol() -> None:
    # Compile-time check/protocol compliance assertion
    provider: LLMProvider = OllamaProvider(base_url="http://localhost:11434", model="test")
    assert provider is not None
