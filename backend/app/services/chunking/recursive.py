from __future__ import annotations
from typing import Any
from backend.app.services.chunking.base import BaseChunker
from backend.app.services.chunking.models import ChunkResult


class RecursiveChunker(BaseChunker):
    """Split text recursively using progressively smaller separators."""

    DEFAULT_SEPARATORS = ("\n\n", "\n", " ", "")

    def chunk(self, text: str, **kwargs:Any) -> list[ChunkResult]:
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

        separators = kwargs.get("separators", self.DEFAULT_SEPARATORS)

        pieces = self._split_recursively(text, chunk_size, separators)
        chunks = self._merge_pieces(pieces, chunk_size, overlap)

        return [
            ChunkResult(
                text=chunk_text,
                start_char=start,
                end_char=end,
                chunk_index=index,
                metadata={
                    "strategy": "recursive",
                    "chunk_size": chunk_size,
                    "overlap": overlap,
                },
            )
            for index, (chunk_text, start, end) in enumerate(chunks)
        ]

    def _split_recursively(
        self,
        text: str,
        chunk_size: int,
        separators: tuple[str, ...],
    ) -> list[tuple[str, int]]:
        if len(text) <= chunk_size:
            return [(text, 0)]

        separator = self._choose_separator(text, separators)

        if separator == "":
            return [
                (text[index : index + chunk_size], index)
                for index in range(0, len(text), chunk_size)
            ]

        parts = text.split(separator)

        pieces: list[tuple[str, int]] = []
        cursor = 0

        for part in parts:
            if not part:
                cursor += len(separator)
                continue

            part_start = text.find(part, cursor)
            part_end = part_start + len(part)

            if len(part) <= chunk_size:
                pieces.append((part, part_start))
            else:
                nested = self._split_recursively(
                    part,
                    chunk_size,
                    separators[1:],
                )

                pieces.extend(
                    (nested_text, part_start + nested_start)
                    for nested_text, nested_start in nested
                )

            cursor = part_end + len(separator)

        return pieces

    @staticmethod
    def _choose_separator(
        text: str,
        separators: tuple[str, ...],
    ) -> str:
        for separator in separators:
            if separator == "" or separator in text:
                return separator

        return ""

    @staticmethod
    def _merge_pieces(
        pieces: list[tuple[str, int]],
        chunk_size: int,
        overlap: int,
    ) -> list[tuple[str, int, int]]:
        chunks: list[tuple[str, int, int]] = []

        current_text = ""
        current_start = 0

        for piece, piece_start in pieces:
            candidate = (
                piece
                if not current_text
                else f"{current_text} {piece}"
            )

            if current_text and len(candidate) > chunk_size:
                chunks.append(
                    (
                        current_text,
                        current_start,
                        current_start + len(current_text),
                    )
                )

                if overlap:
                    overlap_text = current_text[-overlap:]
                    current_text = f"{overlap_text} {piece}"
                    current_start = piece_start - len(overlap_text)
                else:
                    current_text = piece
                    current_start = piece_start
            else:
                if not current_text:
                    current_start = piece_start

                current_text = candidate

        if current_text:
            chunks.append(
                (
                    current_text,
                    current_start,
                    current_start + len(current_text),
                )
            )

        return chunks