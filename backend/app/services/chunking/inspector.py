from __future__ import annotations

from typing import Any

from backend.app.services.chunking.models import ChunkResult


class ChunkInspector:
    """Utility helpers for inspecting chunk quality and metadata."""

    @staticmethod
    def summarize(chunks: list[ChunkResult]) -> dict[str, Any]:
        if not chunks:
            return {
                "count": 0,
                "total_chars": 0,
                "avg_chars": 0,
                "min_chars": 0,
                "max_chars": 0,
            }

        lengths = [len(chunk.text) for chunk in chunks]
        return {
            "count": len(chunks),
            "total_chars": sum(lengths),
            "avg_chars": sum(lengths) / len(lengths),
            "min_chars": min(lengths),
            "max_chars": max(lengths),
        }

    @staticmethod
    def inspect(chunks: list[ChunkResult]) -> list[dict[str, Any]]:
        return [
            {
                "chunk_index": chunk.chunk_index,
                "start_index": chunk.start_index,
                "end_index": chunk.end_index,
                "char_count": len(chunk.text),
                "metadata": chunk.metadata,
            }
            for chunk in chunks
        ]
