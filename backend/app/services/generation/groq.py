from __future__ import annotations

import httpx

from backend.app.services.generation.base import LLMProviderError


class GroqProvider:
    """Groq provider using Groq's OpenAI-compatible completions API endpoint."""

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        context: str,
        query: str,
        system_prompt: str | None = None,
    ) -> str:
        """Translate generate call into Groq completion request."""
        if not self.api_key:
            raise LLMProviderError("Groq API key is not configured.")

        url = f"{self.BASE_URL}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        user_content = f"Context:\n{context}\n\nQuery:\n{query}"
        messages.append({"role": "user", "content": user_content})

        payload = {
            "model": self.model,
            "messages": messages,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                raise LLMProviderError(
                    f"Groq API returned HTTP error: {e.response.status_code}"
                ) from e
            except httpx.RequestError as e:
                raise LLMProviderError(f"Failed to communicate with Groq API: {e}") from e
            except (KeyError, TypeError, IndexError) as e:
                raise LLMProviderError(f"Malformed response format from Groq API: {e}") from e
