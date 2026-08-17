from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.db.models.chunk import Chunk
from backend.app.services.retrieval.service import (
    RetrievalResult,
    RetrievalService,
)


@pytest.mark.asyncio
async def test_search_returns_ranked_chunks() -> None:
    chunk_one = Chunk(
        id=1,
        document_id=10,
        content="User authentication is handled by JWT.",
        chunk_index=0,
        strategy="document_aware",
    )

    chunk_two = Chunk(
        id=2,
        document_id=10,
        content="Products are stored in PostgreSQL.",
        chunk_index=1,
        strategy="document_aware",
    )

    db = MagicMock()

    result = MagicMock()
    result.all.return_value = [
        (chunk_one, 0.95),
        (chunk_two, 0.72),
    ]

    db.execute = AsyncMock(return_value=result)

    service = RetrievalService(db=db)

    results = await service.search(
        query_embedding=[0.1] * 1024,
        top_k=2,
    )

    assert len(results) == 2

    assert isinstance(results[0], RetrievalResult)
    assert results[0].chunk is chunk_one
    assert results[0].score == 0.95

    assert results[1].chunk is chunk_two
    assert results[1].score == 0.72

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_returns_empty_when_no_chunks_match() -> None:
    db = MagicMock()

    result = MagicMock()
    result.all.return_value = []

    db.execute = AsyncMock(return_value=result)

    service = RetrievalService(db=db)

    results = await service.search(
        query_embedding=[0.1] * 1024,
    )

    assert results == []
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_rejects_empty_query_embedding() -> None:
    db = MagicMock()

    service = RetrievalService(db=db)

    with pytest.raises(
        ValueError,
        match="query_embedding must not be empty",
    ):
        await service.search(
            query_embedding=[],
        )

    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_search_rejects_invalid_top_k() -> None:
    db = MagicMock()

    service = RetrievalService(db=db)

    with pytest.raises(
        ValueError,
        match="top_k must be greater than 0",
    ):
        await service.search(
            query_embedding=[0.1] * 1024,
            top_k=0,
        )

    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_search_supports_repository_filter() -> None:
    db = MagicMock()

    result = MagicMock()
    result.all.return_value = []

    db.execute = AsyncMock(return_value=result)

    service = RetrievalService(db=db)

    await service.search(
        query_embedding=[0.1] * 1024,
        repository_id=42,
    )

    db.execute.assert_awaited_once()

    query = db.execute.await_args.args[0]
    sql = str(query)

    assert "documents.repository_id" in sql


@pytest.mark.asyncio
async def test_search_supports_document_filter() -> None:
    db = MagicMock()

    result = MagicMock()
    result.all.return_value = []

    db.execute = AsyncMock(return_value=result)

    service = RetrievalService(db=db)

    await service.search(
        query_embedding=[0.1] * 1024,
        document_id=7,
    )

    db.execute.assert_awaited_once()

    query = db.execute.await_args.args[0]
    sql = str(query)

    assert "chunks.document_id" in sql


@pytest.mark.asyncio
async def test_search_applies_top_k() -> None:
    db = MagicMock()

    result = MagicMock()
    result.all.return_value = []

    db.execute = AsyncMock(return_value=result)

    service = RetrievalService(db=db)

    await service.search(
        query_embedding=[0.1] * 1024,
        top_k=5,
    )

    db.execute.assert_awaited_once()

    query = db.execute.await_args.args[0]

    assert query._limit_clause is not None
    assert query._limit_clause.value == 5
