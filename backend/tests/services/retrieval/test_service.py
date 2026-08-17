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


@pytest.mark.asyncio
async def test_search_bm25_strategy_scores_correctly() -> None:
    chunk_one = Chunk(
        id=1,
        document_id=10,
        content="This contains keyword banana apple orange.",
        chunk_index=0,
        strategy="document_aware",
    )
    chunk_two = Chunk(
        id=2,
        document_id=10,
        content="This contains keyword banana only.",
        chunk_index=1,
        strategy="document_aware",
    )

    db = MagicMock()
    result = MagicMock()
    # Mock return value of db.execute for bm25 strategy (which uses scalars().all())
    result.scalars.return_value.all.return_value = [chunk_one, chunk_two]
    db.execute = AsyncMock(return_value=result)

    service = RetrievalService(db=db)

    # Search for "apple orange"
    results = await service.search(
        query_text="apple orange",
        strategy="bm25",
        top_k=2,
    )

    # chunk_one has both keywords, so it should rank first with score > 0
    assert len(results) == 1
    assert results[0].chunk is chunk_one
    assert results[0].score > 0.0


@pytest.mark.asyncio
async def test_search_bm25_rejects_missing_query_text() -> None:
    db = MagicMock()
    service = RetrievalService(db=db)

    with pytest.raises(ValueError, match="query_text must not be empty"):
        await service.search(strategy="bm25", query_text="")


@pytest.mark.asyncio
async def test_search_hybrid_strategy_applies_rrf() -> None:
    chunk_dense = Chunk(id=1, content="dense chunk", voyage_embedding=[0.1] * 1024)
    chunk_bm25 = Chunk(id=2, content="bm25 chunk matching query")
    chunk_both = Chunk(
        id=3,
        content="both dense and bm25 chunk matching query",
        voyage_embedding=[0.1] * 1024,
    )

    db = MagicMock()
    
    # We will mock the search method on the service directly to return predetermined ranked lists
    service = RetrievalService(db=db)
    
    # Mocking internal search calls by subclassing or patch could work, but a cleaner way
    # is to mock self.db.execute to return appropriate results for the sub-calls.
    # The first sub-call is "dense" (returns database rows)
    # The second sub-call is "bm25" (returns scalars)
    
    execute_mock = AsyncMock()
    db.execute = execute_mock
    
    # Prepare result for Dense call
    dense_result = MagicMock()
    dense_result.all.return_value = [
        (chunk_both, 0.99), # rank 1
        (chunk_dense, 0.90), # rank 2
    ]
    
    # Prepare result for BM25 call
    bm25_result = MagicMock()
    bm25_result.scalars.return_value.all.return_value = [
        chunk_both, # rank 1
        chunk_bm25, # rank 2
    ]
    
    execute_mock.side_effect = [dense_result, bm25_result]
    
    results = await service.search(
        query_text="matching query",
        query_embedding=[0.1]*1024,
        strategy="hybrid",
        top_k=3,
    )
    
    # RRF rank 1: chunk_both (rank 1 dense, rank 2 bm25) -> score: 1/(60+1) + 1/(60+2) = ~0.0325
    # RRF rank 2: chunk_bm25 (rank 1 bm25) -> score: 1/(60+1) = ~0.0164
    # RRF rank 3: chunk_dense (rank 2 dense) -> score: 1/(60+2) = ~0.0161
    
    assert len(results) == 3
    assert results[0].chunk is chunk_both
    assert results[1].chunk is chunk_bm25
    assert results[2].chunk is chunk_dense
    
    # Verify RRF scores
    assert abs(results[0].score - (1.0/61.0 + 1.0/62.0)) < 1e-6
    assert abs(results[1].score - (1.0/61.0)) < 1e-6
    assert abs(results[2].score - (1.0/62.0)) < 1e-6


@pytest.mark.asyncio
async def test_search_rejects_unknown_strategy() -> None:
    db = MagicMock()
    service = RetrievalService(db=db)

    with pytest.raises(ValueError, match="Unknown retrieval strategy"):
        await service.search(strategy="invalid_strategy")

