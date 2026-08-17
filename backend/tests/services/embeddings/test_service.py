from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.db.models.chunk import Chunk
from backend.app.services.embeddings.service import EmbeddingService


@pytest.mark.asyncio
async def test_embed_chunks_batches_requests() -> None:
    chunks = [
        Chunk(
            id=1,
            document_id=1,
            content="chunk one",
            chunk_index=0,
            strategy="fixed",
        ),
        Chunk(
            id=2,
            document_id=1,
            content="chunk two",
            chunk_index=1,
            strategy="fixed",
        ),
        Chunk(
            id=3,
            document_id=1,
            content="chunk three",
            chunk_index=2,
            strategy="fixed",
        ),
    ]

    provider = MagicMock()
    provider.dimensions = 1024
    provider.embed_documents = AsyncMock(
        side_effect=[
            [[0.1] * 1024, [0.2] * 1024],
            [[0.3] * 1024],
        ],
    )

    db = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = chunks
    db.execute = AsyncMock(return_value=result)
    db.flush = AsyncMock()
    db.commit = AsyncMock()

    service = EmbeddingService(
        db=db,
        provider=provider,
        batch_size=2,
    )

    count = await service.embed_chunks()

    assert count == 3

    assert provider.embed_documents.await_count == 2

    provider.embed_documents.assert_any_await(
        ["chunk one", "chunk two"],
    )
    provider.embed_documents.assert_awaited_with(
        ["chunk three"],
    )

    assert chunks[0].voyage_embedding == [0.1] * 1024
    assert chunks[1].voyage_embedding == [0.2] * 1024
    assert chunks[2].voyage_embedding == [0.3] * 1024

    db.flush.assert_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_embed_chunks_returns_zero_when_nothing_needs_embedding() -> None:
    provider = MagicMock()
    provider.dimensions = 1024
    provider.embed_documents = AsyncMock()

    db = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()

    service = EmbeddingService(
        db=db,
        provider=provider,
    )

    count = await service.embed_chunks()

    assert count == 0
    provider.embed_documents.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_embed_chunks_rejects_wrong_embedding_count() -> None:
    chunks = [
        Chunk(
            id=1,
            document_id=1,
            content="chunk one",
            chunk_index=0,
            strategy="fixed",
        ),
        Chunk(
            id=2,
            document_id=1,
            content="chunk two",
            chunk_index=1,
            strategy="fixed",
        ),
    ]

    provider = MagicMock()
    provider.dimensions = 1024
    provider.embed_documents = AsyncMock(
        return_value=[[0.1] * 1024],
    )

    db = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = chunks
    db.execute = AsyncMock(return_value=result)

    service = EmbeddingService(
        db=db,
        provider=provider,
    )

    with pytest.raises(
        ValueError,
        match="different number of embeddings",
    ):
        await service.embed_chunks()
