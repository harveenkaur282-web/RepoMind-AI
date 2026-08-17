from __future__ import annotations

from typing import Protocol


class LLMProviderError(Exception):
    """Domain-level exception for LLM provider errors."""

    pass


class LLMProvider(Protocol):
    """Protocol defining the interface for an LLM text generation provider."""

    async def generate(
        self,
        context: str,
        query: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate text response using context and user query."""
        ...
