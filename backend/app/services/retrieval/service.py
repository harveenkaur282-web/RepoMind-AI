from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.chunk import Chunk
from backend.app.db.models.document import Document


@dataclass(slots=True)
class RetrievalResult:
    """A chunk returned by vector similarity search."""

    chunk: Chunk
    score: float


class RetrievalService:
    """Retrieve relevant chunks using vector similarity search."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        repository_id: int | None = None,
        document_id: int | None = None,
    ) -> list[RetrievalResult]:
        """Return the most similar chunks for a query embedding."""

        if not query_embedding:
            raise ValueError("query_embedding must not be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        distance = Chunk.voyage_embedding.cosine_distance(
            query_embedding,
        )

        query = (
            select(
                Chunk,
                (1 - distance).label("score"),
            )
            .join(Document, Chunk.document_id == Document.id)
            .where(
                Chunk.voyage_embedding.is_not(None),
            )
        )

        if repository_id is not None:
            query = query.where(
                Document.repository_id == repository_id,
            )

        if document_id is not None:
            query = query.where(
                Chunk.document_id == document_id,
            )

        query = query.order_by(distance).limit(top_k)

        result = await self.db.execute(query)

        return [
            RetrievalResult(
                chunk=chunk,
                score=float(score),
            )
            for chunk, score in result.all()
        ]
