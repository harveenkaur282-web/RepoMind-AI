from __future__ import annotations

import typing
from collections.abc import Callable
from dataclasses import dataclass

from backend.app.db.models.chunk import Chunk

if typing.TYPE_CHECKING:
    from backend.app.services.retrieval.service import RetrievalResult


@dataclass(slots=True)
class AssembledContext:
    """Assembled context payload for generation step."""

    context_str: str
    chunks: list[Chunk]
    total_chunks: int
    total_tokens: int


class ContextAssembler:
    """Assembles retrieved chunks into structured context."""

    def __init__(
        self,
        max_chunks: int | None = None,
        max_tokens: int | None = None,
        token_estimator: Callable[[str], int] | None = None,
    ) -> None:
        self.max_chunks = max_chunks
        self.max_tokens = max_tokens
        # Simple estimator: 1 token ~ 4 characters
        self.token_estimator = token_estimator or (lambda x: len(x) // 4)

    def assemble(self, results: list[RetrievalResult]) -> AssembledContext:
        """Deduplicate, format, and limit retrieved chunks into context."""
        # 1. Deduplicate while preserving order
        seen_ids = set()
        unique_results = []
        for res in results:
            if res.chunk.id not in seen_ids:
                seen_ids.add(res.chunk.id)
                unique_results.append(res)

        assembled_chunks: list[Chunk] = []
        formatted_parts: list[str] = []
        current_tokens = 0

        # Helper to format a single chunk
        def format_chunk(chunk: Chunk) -> str:
            path = "Unknown"
            if hasattr(chunk, "document") and chunk.document:
                path = chunk.document.path or "Unknown"
            return f"---\nDocument: {path}\nContent:\n{chunk.content}\n"

        for res in unique_results:
            # Check max_chunks limit
            if self.max_chunks is not None and len(assembled_chunks) >= self.max_chunks:
                break

            chunk_str = format_chunk(res.chunk)
            chunk_tokens = self.token_estimator(chunk_str)

            # Check max_tokens limit
            if self.max_tokens is not None:
                # If adding this chunk exceeds max_tokens, we stop to avoid breaking limits
                if current_tokens + chunk_tokens > self.max_tokens:
                    break

            assembled_chunks.append(res.chunk)
            formatted_parts.append(chunk_str)
            current_tokens += chunk_tokens

        context_str = "".join(formatted_parts)

        return AssembledContext(
            context_str=context_str,
            chunks=assembled_chunks,
            total_chunks=len(assembled_chunks),
            total_tokens=current_tokens,
        )
