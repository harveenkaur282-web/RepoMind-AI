from __future__ import annotations

import re

from backend.app.services.rag.reranker.base import Reranker
from backend.app.services.retrieval.service import RetrievalResult


class LocalCrossEncoderReranker(Reranker):
    """Lightweight, dependency-free local reranker simulating a cross-encoder.

    Optimized for code search by matching programming identifiers, CamelCase,
    snake_case, and path structures.
    """

    def __init__(self, model_name: str = "local-cross-encoder") -> None:
        self.model_name = model_name

    def _tokenize(self, text: str) -> list[str]:
        """Split text into lowercase sub-tokens, breaking CamelCase/snake_case/symbols."""
        # Break camelCase
        decamel = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
        # Break snake_case and non-alphanumeric chars
        words = re.findall(r"[a-zA-Z0-9]+", decamel.lower())
        return words

    async def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """Rerank candidates based on keyword matching and code identifier relevance."""
        if not candidates:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            for c in candidates:
                c.rerank_score = 0.0
            return candidates

        query_token_set = set(query_tokens)
        reranked_results = []

        for candidate in candidates:
            doc_text = candidate.chunk.content
            doc_tokens = self._tokenize(doc_text)
            doc_token_set = set(doc_tokens)

            # 1. Term overlap score
            overlap = query_token_set.intersection(doc_token_set)
            term_score = len(overlap) / len(query_token_set)

            # 2. Path matching boost: if candidate belongs to a document, match path components
            path_score = 0.0
            if candidate.chunk.document and candidate.chunk.document.path:
                path_tokens = set(self._tokenize(candidate.chunk.document.path))
                path_overlap = query_token_set.intersection(path_tokens)
                path_score = len(path_overlap) / len(query_token_set) * 0.5

            # 3. Phrase match bonus: check if sequence of query words occurs exactly in doc
            phrase_score = 0.0
            query_phrase = " ".join(query_tokens)
            doc_phrase = " ".join(doc_tokens)
            if query_phrase in doc_phrase:
                phrase_score = 0.3

            # Calculate total rerank score and clamp between 0.0 and 1.0
            total_score = min(term_score + path_score + phrase_score, 1.0)
            candidate.rerank_score = total_score
            reranked_results.append(candidate)

        # Sort candidates descending by rerank score, falling back to original retrieval score
        reranked_results.sort(key=lambda x: (x.rerank_score or 0.0, x.score), reverse=True)
        return reranked_results
