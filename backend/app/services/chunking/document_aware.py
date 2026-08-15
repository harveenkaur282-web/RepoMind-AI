from __future__ import annotations

from typing import Any

from backend.app.services.chunking.base import BaseChunker
from backend.app.services.chunking.models import ChunkResult


class DocumentAwareChunker(BaseChunker):
    """Chunker that prefers structural document boundaries like headings."""

    def chunk(self, text: str, **kwargs: Any) -> list[ChunkResult]:
        if not text:
            return []

        chunk_size = kwargs.get("chunk_size", self.config.chunk_size)
        overlap = kwargs.get("overlap", self.config.overlap)
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        segments: list[str] = []
        current: list[str] = []
        current_length = 0

        for line in text.splitlines():
            line_text = line.rstrip()
            if not line_text:
                if current:
                    segments.append("\n".join(current))
                    current = []
                    current_length = 0
                continue

            if current and current_length + len(line_text) > chunk_size:
                segments.append("\n".join(current))
                current = [line_text]
                current_length = len(line_text)
            else:
                current.append(line_text)
                current_length += len(line_text)

        if current:
            segments.append("\n".join(current))

        chunks: list[ChunkResult] = []
        for index, segment in enumerate(segments):
            if len(segment) < self.config.min_chunk_size and chunks:
                chunks[-1].text = f"{chunks[-1].text}\n\n{segment}"
                continue

            chunks.append(
                ChunkResult(
                    text=segment,
                    start_index=0,
                    end_index=len(segment),
                    chunk_index=index,
                    metadata={"strategy": "document_aware"},
                )
            )

        if overlap and chunks:
            for index in range(1, len(chunks)):
                current_chunk = chunks[index]
                previous_chunk = chunks[index - 1]
                current_chunk.start_index = previous_chunk.end_index - overlap
                current_chunk.end_index = current_chunk.start_index + len(current_chunk.text)

        return chunks

    def chunk_document(self, document: Any, **kwargs: Any) -> list[ChunkResult]:
        text = getattr(document, "content", str(document))
        return self.chunk(str(text), **kwargs)
