from __future__ import annotations

import httpx

from backend.app.services.generation.base import LLMProviderError


class OllamaProvider:
    """Ollama provider for local text generation."""

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(
        self,
        context: str,
        query: str,
        system_prompt: str | None = None,
    ) -> str:
        """Translate generate call into Ollama /api/chat request."""
        url = f"{self.base_url}/api/chat"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        user_content = f"Context:\n{context}\n\nQuery:\n{query}"
        messages.append({"role": "user", "content": user_content})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]
            except httpx.HTTPStatusError as e:
                raise LLMProviderError(
                    f"Ollama server returned HTTP error: {e.response.status_code}"
                ) from e
            except httpx.RequestError as e:
                raise LLMProviderError(f"Failed to communicate with Ollama server: {e}") from e
            except (KeyError, TypeError) as e:
                raise LLMProviderError(f"Malformed response format from Ollama server: {e}") from e
