from __future__ import annotations

from typing import Any

from backend.app.services.chunking.base import BaseChunker
from backend.app.services.chunking.models import ChunkResult


class RecursiveChunker(BaseChunker):
    """Chunk text by splitting on semantic separators and recursively shrinking."""

    def chunk(self, text: str, **kwargs: Any) -> list[ChunkResult]:
        if not text:
            return []

        chunk_size = kwargs.get("chunk_size", self.config.chunk_size)
        overlap = kwargs.get("overlap", self.config.overlap)
        separator = kwargs.get("separator", self.config.separator)
        min_chunk_size = kwargs.get("min_chunk_size", self.config.min_chunk_size)

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        parts = text.split(separator)
        chunks: list[ChunkResult] = []
        current = ""
        start_index = 0
        chunk_index = 0

        for part in parts:
            candidate = f"{current}{separator if current else ''}{part}".strip()
            if len(candidate) <= chunk_size:
                current = candidate
                continue

            if current:
                chunk_text = current
                chunks.append(
                    ChunkResult(
                        text=chunk_text,
                        start_index=start_index,
                        end_index=start_index + len(chunk_text),
                        chunk_index=chunk_index,
                        metadata={"strategy": "recursive", "separator": separator},
                    )
                )
                start_index += len(chunk_text) - overlap
                chunk_index += 1
                current = part
            else:
                current = part

        if current and len(current) >= min_chunk_size:
            chunks.append(
                ChunkResult(
                    text=current,
                    start_index=start_index,
                    end_index=start_index + len(current),
                    chunk_index=chunk_index,
                    metadata={"strategy": "recursive", "separator": separator},
                )
            )

        return chunks

    def chunk_document(self, document: Any, **kwargs: Any) -> list[ChunkResult]:
        text = getattr(document, "content", str(document))
        return self.chunk(str(text), **kwargs)
