from __future__ import annotations

from typing import Protocol

from backend.app.services.retrieval.service import RetrievalResult


class Reranker(Protocol):
    """Protocol defining the interface for document/code rerankers."""

    async def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """Rerank retrieval candidates according to relevance to the search query."""
        ...
