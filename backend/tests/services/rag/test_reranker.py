from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.db.models.chunk import Chunk
from backend.app.db.models.document import Document
from backend.app.services.rag.reranker.local import LocalCrossEncoderReranker
from backend.app.services.rag.service import RAGService
from backend.app.services.retrieval.service import RetrievalResult


@pytest.fixture
def sample_candidates() -> list[RetrievalResult]:
    doc = Document(id=1, path="src/database/connection.py")
    chunk1 = Chunk(id=101, content="def get_connection(): return db_conn", document=doc)
    chunk2 = Chunk(id=102, content="import math; print(math.pi)", document=doc)
    chunk3 = Chunk(id=103, content="def query_database(): execute_sql()", document=doc)

    return [
        RetrievalResult(chunk=chunk1, score=0.9),  # Matches get_connection
        RetrievalResult(chunk=chunk2, score=0.8),  # Matches math
        RetrievalResult(chunk=chunk3, score=0.7),  # Matches query_database
    ]


@pytest.mark.asyncio
async def test_local_cross_encoder_rerank_ordering(
    sample_candidates: list[RetrievalResult],
) -> None:
    reranker = LocalCrossEncoderReranker()
    # Query database specifically
    query = "database query SQL connection"

    results = await reranker.rerank(query, sample_candidates)

    # Verify sorting order: chunk3 (database, query, sql) and chunk1 (connection)
    # should rank higher than math (chunk2)
    assert results[0].chunk.id == 103  # "def query_database(): execute_sql()"
    assert results[1].chunk.id == 101  # "def get_connection(): return db_conn"
    assert results[2].chunk.id == 102  # math

    # Verify scores are attached
    assert results[0].rerank_score is not None
    assert results[1].rerank_score is not None
    assert results[0].rerank_score >= results[1].rerank_score


@pytest.mark.asyncio
async def test_reranker_handles_empty_candidates() -> None:
    reranker = LocalCrossEncoderReranker()
    results = await reranker.rerank("query", [])
    assert results == []


@pytest.mark.asyncio
async def test_rag_pipeline_without_reranking(
    sample_candidates: list[RetrievalResult],
) -> None:
    mock_retrieval = MagicMock()
    mock_retrieval.search = AsyncMock(return_value=list(sample_candidates))

    mock_assembler = MagicMock()
    mock_assembler.assemble = MagicMock()
    mock_assembler.assemble.return_value.context_str = "Clean context"
    mock_assembler.assemble.return_value.chunks = []
    mock_assembler.assemble.return_value.total_chunks = 0
    mock_assembler.assemble.return_value.total_tokens = 0

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="Answer")

    rag_service = RAGService(
        retrieval_service=mock_retrieval,
        context_assembler=mock_assembler,
        llm_provider=mock_llm,
        reranker=None,
    )

    response = await rag_service.answer_query(
        query="database query",
        rerank=False,
    )

    # Retrieval order is preserved, search gets top_k=10 by default
    mock_retrieval.search.assert_awaited_once_with(
        query_text="database query",
        query_embedding=None,
        strategy="dense",
        repository_id=None,
        document_id=None,
        top_k=10,
    )
    assert response.results == sample_candidates
    for c in response.results:
        assert c.rerank_score is None


@pytest.mark.asyncio
async def test_rag_pipeline_with_reranking_limit_and_flow(
    sample_candidates: list[RetrievalResult],
) -> None:
    mock_retrieval = MagicMock()
    mock_retrieval.search = AsyncMock(return_value=list(sample_candidates))

    mock_assembler = MagicMock()
    mock_assembler.assemble = MagicMock()
    mock_assembler.assemble.return_value.context_str = "Assembled"
    mock_assembler.assemble.return_value.chunks = []
    mock_assembler.assemble.return_value.total_chunks = 0
    mock_assembler.assemble.return_value.total_tokens = 0

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="Answer")

    mock_reranker = MagicMock()
    # Mock rerank to just return candidates in reverse order
    mock_reranker.rerank = AsyncMock(return_value=list(reversed(sample_candidates)))

    rag_service = RAGService(
        retrieval_service=mock_retrieval,
        context_assembler=mock_assembler,
        llm_provider=mock_llm,
        reranker=mock_reranker,
    )

    response = await rag_service.answer_query(
        query="find database connection",
        rerank=True,
        rerank_limit=50,
    )

    # 1. Retrieval must query with top_k = rerank_limit (50)
    mock_retrieval.search.assert_awaited_once_with(
        query_text="find database connection",
        query_embedding=None,
        strategy="dense",
        repository_id=None,
        document_id=None,
        top_k=50,
    )

    # 2. Reranker should be called with query and retrieved candidates
    mock_reranker.rerank.assert_awaited_once_with(
        query="find database connection",
        candidates=sample_candidates,
    )

    # 3. Order is reversed by mock reranker
    assert response.results[0].chunk.id == 103
    assert response.results[1].chunk.id == 102
    assert response.results[2].chunk.id == 101


@pytest.mark.asyncio
async def test_reranker_errors_propagate_cleanly() -> None:
    mock_retrieval = MagicMock()
    mock_retrieval.search = AsyncMock(return_value=[RetrievalResult(chunk=MagicMock(), score=0.5)])

    mock_reranker = MagicMock()
    mock_reranker.rerank = AsyncMock(side_effect=RuntimeError("Cross-encoder failure"))

    rag_service = RAGService(
        retrieval_service=mock_retrieval,
        context_assembler=MagicMock(),
        llm_provider=MagicMock(),
        reranker=mock_reranker,
    )

    with pytest.raises(RuntimeError, match="Cross-encoder failure"):
        await rag_service.answer_query(query="vague", rerank=True)
