from __future__ import annotations

from backend.app.services.generation.base import LLMProvider


class QueryRewriter:
    """Provider-agnostic query rewriter using an LLMProvider to optimize queries for code search."""

    SYSTEM_PROMPT = (
        "You are a code search optimizer. Rewrite the user's input query into a single "
        "concise search query optimized for codebase search. Preserve technical terms, "
        "names, and files. Strip conversational filler. Respond ONLY with the search query."
    )

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    async def rewrite(self, query: str) -> str:
        """Rewrite the user query into a concise search query optimized for codebase lookup."""
        try:
            rewritten = await self.llm_provider.generate(
                context="",  # Standalone query rewriting requires no context
                query=query,
                system_prompt=self.SYSTEM_PROMPT,
            )
            return rewritten.strip().strip('"').strip("'")
        except Exception as exc:
            raise RuntimeError(f"Query rewriting failed: {exc}") from exc
