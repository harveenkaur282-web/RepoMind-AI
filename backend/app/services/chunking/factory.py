from __future__ import annotations

from backend.app.services.chunking.base import BaseChunker
from backend.app.services.chunking.document_aware import DocumentAwareChunker
from backend.app.services.chunking.fixed import FixedSizeChunker
from backend.app.services.chunking.models import ChunkingConfig
from backend.app.services.chunking.recursive import RecursiveChunker


class ChunkerFactory:
    """Construct chunkers by strategy name."""

    _registry: dict[str, type[BaseChunker]] = {
        "fixed": FixedSizeChunker,
        "recursive": RecursiveChunker,
        "document_aware": DocumentAwareChunker,
    }

    @classmethod
    def get(
        cls,
        strategy: str,
        config: ChunkingConfig | None = None,
    ) -> BaseChunker:
        try:
            chunker_cls = cls._registry[strategy.lower()]
        except KeyError as exc:
            valid = ", ".join(sorted(cls._registry))
            raise ValueError(f"Unsupported chunking strategy: {strategy}. Valid: {valid}") from exc

        return chunker_cls(config=config)

    @classmethod
    def available_strategies(cls) -> list[str]:
        return sorted(cls._registry)
