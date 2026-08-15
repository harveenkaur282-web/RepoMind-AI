from __future__ import annotations

from backend.app.services.chunking.base import BaseChunker
from backend.app.services.chunking.models import ChunkResult


class FixedSizeChunker(BaseChunker):
    """Simple fixed-size chunker based on character windows with overlap."""

    def chunk(self, text: str, **kwargs) -> list[ChunkResult]:
        if not text:
            return []

        chunk_size = kwargs.get("chunk_size", self.config.chunk_size)
        overlap = kwargs.get("overlap", self.config.overlap)

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if overlap < 0:
            raise ValueError("overlap must be non-negative")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        chunks: list[ChunkResult] = []
        start = 0
        index = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            snippet = text[start:end]

            chunks.append(
                ChunkResult(
                    text=snippet,
                    start_char=start,
                    end_char=end,
                    chunk_index=index,
                    metadata={
                        "strategy": "fixed",
                        "chunk_size": chunk_size,
                        "overlap": overlap,
                    },
                )
            )

            index += 1

            if end == len(text):
                break

            start = end - overlap

        return chunks
