from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ChunkingConfig:
    """Configuration used by repository chunking strategies."""

    chunk_size: int = 800
    overlap: int = 120
    min_chunk_size: int = 100
    separator: str = "\n\n"
    respect_headings: bool = True
    include_metadata: bool = True
    max_chunks: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ChunkResult:
    """A chunk produced from a document."""

    text: str
    start_char: int = 0
    end_char: int = 0
    chunk_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
