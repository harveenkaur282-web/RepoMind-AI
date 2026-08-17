from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.db.models.chunk import Chunk
from backend.app.services.generation.base import LLMProviderError
from backend.app.services.rag.service import RAGResponse, RAGService
from backend.app.services.retrieval.context import AssembledContext
from backend.app.services.retrieval.service import RetrievalResult


@pytest.mark.asyncio
async def test_rag_service_success() -> None:
    # 1. Setup mock dependencies
    mock_retrieval = MagicMock()
    mock_assembler = MagicMock()
    mock_llm = MagicMock()

    chunk1 = Chunk(id=1, content="mock content 1")
    results = [RetrievalResult(chunk=chunk1, score=0.9)]
    mock_retrieval.search = AsyncMock(return_value=results)

    assembled = AssembledContext(
        context_str="Assembled content string",
        chunks=[chunk1],
        total_chunks=1,
        total_tokens=5,
    )
    mock_assembler.assemble.return_value = assembled

    mock_llm.generate = AsyncMock(return_value="LLM response output answer.")

    # 2. Instantiate orchestrator
    rag_service = RAGService(
        retrieval_service=mock_retrieval,
        context_assembler=mock_assembler,
        llm_provider=mock_llm,
    )

    # 3. Call method
    response = await rag_service.answer_query(
        query="test query",
        query_embedding=[0.1] * 1024,
        strategy="hybrid",
        repository_id=42,
        system_prompt="Custom sys prompt",
    )

    # 4. Assertions
    assert isinstance(response, RAGResponse)
    assert response.answer == "LLM response output answer."
    assert response.chunks == [chunk1]
    assert response.strategy == "hybrid"
    assert response.total_chunks == 1
    assert response.total_tokens == 5

    # Check dependency invocations
    mock_retrieval.search.assert_awaited_once_with(
        query_text="test query",
        query_embedding=[0.1] * 1024,
        strategy="hybrid",
        repository_id=42,
        document_id=None,
    )
    mock_assembler.assemble.assert_called_once_with(results)
    mock_llm.generate.assert_awaited_once_with(
        context="Assembled content string",
        query="test query",
        system_prompt="Custom sys prompt",
    )


@pytest.mark.asyncio
async def test_rag_service_empty_retrieval() -> None:
    mock_retrieval = MagicMock()
    mock_assembler = MagicMock()
    mock_llm = MagicMock()

    mock_retrieval.search = AsyncMock(return_value=[])

    assembled = AssembledContext(
        context_str="",
        chunks=[],
        total_chunks=0,
        total_tokens=0,
    )
    mock_assembler.assemble.return_value = assembled
    mock_llm.generate = AsyncMock(return_value="No context answer.")

    rag_service = RAGService(
        retrieval_service=mock_retrieval,
        context_assembler=mock_assembler,
        llm_provider=mock_llm,
    )

    response = await rag_service.answer_query(
        query="empty query",
        strategy="bm25",
    )

    assert response.answer == "No context answer."
    assert response.chunks == []
    assert response.total_chunks == 0
    assert response.total_tokens == 0

    mock_retrieval.search.assert_awaited_once_with(
        query_text="empty query",
        query_embedding=None,
        strategy="bm25",
        repository_id=None,
        document_id=None,
    )
    mock_assembler.assemble.assert_called_once_with([])
    mock_llm.generate.assert_awaited_once_with(
        context="",
        query="empty query",
        system_prompt=None,
    )


@pytest.mark.asyncio
async def test_rag_service_retrieval_error_propagation() -> None:
    mock_retrieval = MagicMock()
    mock_assembler = MagicMock()
    mock_llm = MagicMock()

    mock_retrieval.search = AsyncMock(side_effect=ValueError("Invalid strategy"))

    rag_service = RAGService(
        retrieval_service=mock_retrieval,
        context_assembler=mock_assembler,
        llm_provider=mock_llm,
    )

    with pytest.raises(ValueError, match="Invalid strategy"):
        await rag_service.answer_query(query="test", strategy="invalid")


@pytest.mark.asyncio
async def test_rag_service_generation_error_propagation() -> None:
    mock_retrieval = MagicMock()
    mock_assembler = MagicMock()
    mock_llm = MagicMock()

    mock_retrieval.search = AsyncMock(return_value=[])
    mock_assembler.assemble.return_value = AssembledContext(
        context_str="", chunks=[], total_chunks=0, total_tokens=0
    )
    mock_llm.generate = AsyncMock(side_effect=LLMProviderError("Ollama offline"))

    rag_service = RAGService(
        retrieval_service=mock_retrieval,
        context_assembler=mock_assembler,
        llm_provider=mock_llm,
    )

    with pytest.raises(LLMProviderError, match="Ollama offline"):
        await rag_service.answer_query(query="test")
