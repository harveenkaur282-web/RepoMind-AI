from __future__ import annotations

from abc import ABC, abstractmethod

from backend.app.services.chunking.models import ChunkingConfig, ChunkResult


class BaseChunker(ABC):
    """Base interface for document chunking strategies."""

    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self.config = config or ChunkingConfig()

    @abstractmethod
    def chunk(self, text: str) -> list[ChunkResult]:
        """Split document text into chunks."""
        raise NotImplementedError
