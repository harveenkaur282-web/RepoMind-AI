from __future__ import annotations

import re
from typing import Any

from backend.app.services.chunking.base import BaseChunker
from backend.app.services.chunking.models import ChunkResult


class DocumentAwareChunker(BaseChunker):
    """Chunk documents while preserving document-specific structure."""

    CODE_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".cs",
        ".swift",
        ".kt",
    }

    MARKDOWN_EXTENSIONS = {
        ".md",
        ".markdown",
        ".mdx",
    }

    def chunk(
        self,
        text: str,
        **kwargs: Any,
    ) -> list[ChunkResult]:
        """Chunk plain text using document-aware heuristics."""

        document_type = kwargs.get("document_type", "text")
        path = str(kwargs.get("path", "")).lower()

        if not text:
            return []

        if document_type in {"issue", "pull_request", "release"}:
            return self._chunk_structured_content(text, document_type, kwargs)

        if self._is_markdown(path, document_type):
            return self._chunk_markdown(text, kwargs)

        if self._is_code(path, document_type):
            return self._chunk_code(text, kwargs)

        return self._chunk_paragraphs(text, kwargs)

    def chunk_document(
        self,
        document: Any,
        **kwargs: Any,
    ) -> list[ChunkResult]:
        """Chunk a repository Document using its metadata."""

        text = str(getattr(document, "content", ""))

        document_type = getattr(document, "document_type", "text")
        path = str(getattr(document, "path", ""))

        return self.chunk(
            text,
            document_type=document_type,
            path=path,
            **kwargs,
        )

    def _chunk_markdown(
        self,
        text: str,
        kwargs: dict[str, Any],
    ) -> list[ChunkResult]:
        """Preserve Markdown heading and code-block boundaries."""

        chunk_size = kwargs.get(
            "chunk_size",
            self.config.chunk_size,
        )

        sections = self._split_markdown_sections(text)

        chunks: list[ChunkResult] = []

        for section_text, start, heading in sections:
            if len(section_text) <= chunk_size:
                chunks.append(
                    self._make_chunk(
                        section_text,
                        start,
                        heading=heading,
                        document_type="markdown",
                    )
                )
                continue

            chunks.extend(
                self._split_large_section(
                    section_text,
                    start,
                    chunk_size,
                    heading=heading,
                )
            )

        return self._reindex(chunks)

    def _split_markdown_sections(
        self,
        text: str,
    ) -> list[tuple[str, int, str | None]]:
        """Split Markdown at headings without splitting fenced code blocks."""

        lines = text.splitlines(keepends=True)

        sections: list[tuple[str, int, str | None]] = []

        current_lines: list[str] = []
        current_start = 0
        current_heading: str | None = None
        position = 0
        in_code_block = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("```"):
                in_code_block = not in_code_block

            heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)

            if heading_match and not in_code_block:
                if current_lines:
                    sections.append(
                        (
                            "".join(current_lines),
                            current_start,
                            current_heading,
                        )
                    )

                current_lines = [line]
                current_start = position
                current_heading = heading_match.group(2)
            else:
                current_lines.append(line)

            position += len(line)

        if current_lines:
            sections.append(
                (
                    "".join(current_lines),
                    current_start,
                    current_heading,
                )
            )

        return sections

    def _chunk_code(
        self,
        text: str,
        kwargs: dict[str, Any],
    ) -> list[ChunkResult]:
        """Prefer function/class boundaries for source code."""

        chunk_size = kwargs.get(
            "chunk_size",
            self.config.chunk_size,
        )

        blocks = self._split_code_blocks(text)

        chunks: list[ChunkResult] = []

        for block_text, start, symbol in blocks:
            if len(block_text) <= chunk_size:
                chunks.append(
                    self._make_chunk(
                        block_text,
                        start,
                        symbol=symbol,
                        document_type="code",
                    )
                )
            else:
                chunks.extend(
                    self._split_large_section(
                        block_text,
                        start,
                        chunk_size,
                        symbol=symbol,
                        document_type="code",
                    )
                )

        return self._reindex(chunks)

    def _split_code_blocks(
        self,
        text: str,
    ) -> list[tuple[str, int, str | None]]:
        """Split common source files at top-level classes/functions."""

        lines = text.splitlines(keepends=True)

        blocks: list[tuple[str, int, str | None]] = []

        current_lines: list[str] = []
        current_start = 0
        current_symbol: str | None = None
        position = 0

        pattern = re.compile(
            r"^\s*(?:async\s+)?"
            r"(?:def|class|function|interface|struct|enum)\s+"
            r"([A-Za-z_][A-Za-z0-9_]*)"
        )

        for line in lines:
            match = pattern.match(line)

            if match and current_lines:
                blocks.append(
                    (
                        "".join(current_lines),
                        current_start,
                        current_symbol,
                    )
                )

                current_lines = []
                current_start = position

            if match:
                current_symbol = match.group(1)

            current_lines.append(line)
            position += len(line)

        if current_lines:
            blocks.append(
                (
                    "".join(current_lines),
                    current_start,
                    current_symbol,
                )
            )

        return blocks

    def _chunk_structured_content(
        self,
        text: str,
        document_type: str,
        kwargs: dict[str, Any],
    ) -> list[ChunkResult]:
        """Chunk GitHub issues, PRs and releases by their sections."""

        chunk_size = kwargs.get(
            "chunk_size",
            self.config.chunk_size,
        )

        sections = re.split(
            r"\n(?=#{1,6}\s+)",
            text,
        )

        chunks: list[ChunkResult] = []
        cursor = 0

        for section in sections:
            if not section.strip():
                cursor += len(section)
                continue

            start = text.find(section, cursor)

            if len(section) <= chunk_size:
                chunks.append(
                    self._make_chunk(
                        section,
                        start,
                        document_type=document_type,
                    )
                )
            else:
                chunks.extend(
                    self._split_large_section(
                        section,
                        start,
                        chunk_size,
                        document_type=document_type,
                    )
                )

            cursor = start + len(section)

        return self._reindex(chunks)

    def _chunk_paragraphs(
        self,
        text: str,
        kwargs: dict[str, Any],
    ) -> list[ChunkResult]:
        """Fallback strategy for unstructured documents."""

        chunk_size = kwargs.get(
            "chunk_size",
            self.config.chunk_size,
        )

        paragraphs = re.split(r"\n\s*\n", text)

        chunks: list[ChunkResult] = []
        cursor = 0

        for paragraph in paragraphs:
            if not paragraph.strip():
                cursor += len(paragraph)
                continue

            start = text.find(paragraph, cursor)

            if len(paragraph) <= chunk_size:
                chunks.append(
                    self._make_chunk(
                        paragraph,
                        start,
                        document_type="text",
                    )
                )
            else:
                chunks.extend(
                    self._split_large_section(
                        paragraph,
                        start,
                        chunk_size,
                        document_type="text",
                    )
                )

            cursor = start + len(paragraph)

        return self._reindex(chunks)

    def _split_large_section(
        self,
        text: str,
        start: int,
        chunk_size: int,
        **metadata: Any,
    ) -> list[ChunkResult]:
        """Fallback character splitting for an oversized structural unit."""

        chunks: list[ChunkResult] = []

        for offset in range(0, len(text), chunk_size):
            chunk_text = text[offset : offset + chunk_size]

            chunks.append(
                self._make_chunk(
                    chunk_text,
                    start + offset,
                    **metadata,
                )
            )

        return chunks

    def _make_chunk(
        self,
        text: str,
        start: int,
        **metadata: Any,
    ) -> ChunkResult:
        return ChunkResult(
            text=text,
            start_char=start,
            end_char=start + len(text),
            chunk_index=0,
            metadata={
                "strategy": "document_aware",
                **metadata,
            },
        )

    @staticmethod
    def _reindex(
        chunks: list[ChunkResult],
    ) -> list[ChunkResult]:
        for index, chunk in enumerate(chunks):
            chunk.chunk_index = index

        return chunks

    def _is_markdown(
        self,
        path: str,
        document_type: str,
    ) -> bool:
        if document_type.lower() in {"markdown", "md"}:
            return True

        return any(path.endswith(extension) for extension in self.MARKDOWN_EXTENSIONS)

    def _is_code(
        self,
        path: str,
        document_type: str,
    ) -> bool:
        if document_type.lower() in {"code", "source"}:
            return True

        return any(path.endswith(extension) for extension in self.CODE_EXTENSIONS)