from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.chunk import Chunk
from backend.app.db.models.document import Document
from backend.app.services.embeddings.base import EmbeddingProvider


class EmbeddingService:
    """Generate and persist embeddings for chunks."""

    def __init__(
        self,
        db: AsyncSession,
        provider: EmbeddingProvider,
        batch_size: int = 128,
    ) -> None:
        self.db = db
        self.provider = provider
        self.batch_size = batch_size

    async def embed_chunks(
        self,
        document_id: int | None = None,
        repository_id: int | None = None,
    ) -> int:
        """Embed chunks that do not already have a local embedding."""

        query = select(Chunk).where(
            Chunk.local_embedding.is_(None),
        )

        if document_id is not None:
            query = query.where(
                Chunk.document_id == document_id,
            )

        if repository_id is not None:
            query = query.join(Document).where(
                Document.repository_id == repository_id,
            )

        query = query.order_by(Chunk.id)

        result = await self.db.execute(query)
        chunks = list(result.scalars().all())

        if not chunks:
            return 0

        embedded_count = 0

        for start in range(0, len(chunks), self.batch_size):
            batch = chunks[start : start + self.batch_size]
            texts = [chunk.content for chunk in batch]

            embeddings = await self.provider.embed_documents(texts)

            if len(embeddings) != len(batch):
                raise ValueError(
                    "Embedding provider returned a different number of embeddings than requested."
                )

            for chunk, embedding in zip(batch, embeddings, strict=True):
                if len(embedding) != self.provider.dimensions:
                    raise ValueError(
                        f"Expected embedding dimension "
                        f"{self.provider.dimensions}, "
                        f"got {len(embedding)}."
                    )

                chunk.local_embedding = embedding

            embedded_count += len(batch)

            await self.db.flush()

        await self.db.commit()

        return embedded_count
