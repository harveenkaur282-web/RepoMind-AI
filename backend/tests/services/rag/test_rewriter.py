from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.services.generation.base import LLMProviderError
from backend.app.services.rag.rewriter import QueryRewriter
from backend.app.services.rag.service import RAGService


@pytest.mark.asyncio
async def test_query_rewriter_success() -> None:
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value='  "optimized db config query"  ')

    rewriter = QueryRewriter(mock_llm)
    original_query = "how do I configure the database?"

    rewritten_query = await rewriter.rewrite(original_query)

    # 1. Verify quotes and spaces are cleaned up
    assert rewritten_query == "optimized db config query"
    # 2. Verify original query is unmodified
    assert original_query == "how do I configure the database?"

    # 3. Verify parameters passed to LLM
    mock_llm.generate.assert_awaited_once_with(
        context="",
        query=original_query,
        system_prompt=QueryRewriter.SYSTEM_PROMPT,
    )


@pytest.mark.asyncio
async def test_query_rewriter_error_propagation() -> None:
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(side_effect=LLMProviderError("Ollama timeout"))

    rewriter = QueryRewriter(mock_llm)

    with pytest.raises(RuntimeError, match="Query rewriting failed: Ollama timeout"):
        await rewriter.rewrite("vague query")


@pytest.mark.asyncio
async def test_rag_pipeline_orchestrates_rewriting() -> None:
    mock_retrieval = MagicMock()
    mock_retrieval.search = AsyncMock(return_value=[])

    mock_assembler = MagicMock()
    mock_assembler.assemble = MagicMock()
    mock_assembler.assemble.return_value.context_str = "Code context"
    mock_assembler.assemble.return_value.chunks = []
    mock_assembler.assemble.return_value.total_chunks = 0
    mock_assembler.assemble.return_value.total_tokens = 0

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="RAG Answer")

    rag_service = RAGService(
        retrieval_service=mock_retrieval,
        context_assembler=mock_assembler,
        llm_provider=mock_llm,
    )

    # Flow check: original query is "how is X configured?", search query is "config X"
    response = await rag_service.answer_query(
        query="how is X configured?",
        search_query="config X",
    )

    assert response.answer == "RAG Answer"
    assert response.rewritten_query == "config X"

    # 1. Retrieval must receive the REWRITTEN query
    mock_retrieval.search.assert_awaited_once_with(
        query_text="config X",
        query_embedding=None,
        strategy="dense",
        repository_id=None,
        document_id=None,
        top_k=10,
    )

    # 2. Final LLM Generation must receive the ORIGINAL query
    mock_llm.generate.assert_awaited_once_with(
        context="Code context",
        query="how is X configured?",
        system_prompt=None,
    )


@pytest.mark.asyncio
async def test_rag_pipeline_without_rewriting() -> None:
    mock_retrieval = MagicMock()
    mock_retrieval.search = AsyncMock(return_value=[])

    mock_assembler = MagicMock()
    mock_assembler.assemble = MagicMock()
    mock_assembler.assemble.return_value.context_str = "Context"
    mock_assembler.assemble.return_value.chunks = []
    mock_assembler.assemble.return_value.total_chunks = 0
    mock_assembler.assemble.return_value.total_tokens = 0

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="Answer")

    rag_service = RAGService(
        retrieval_service=mock_retrieval,
        context_assembler=mock_assembler,
        llm_provider=mock_llm,
    )

    # Calling without search_query override
    response = await rag_service.answer_query(query="original search query")

    assert response.answer == "Answer"
    assert response.rewritten_query is None

    # Retrieval and generation both get original query
    mock_retrieval.search.assert_awaited_once_with(
        query_text="original search query",
        query_embedding=None,
        strategy="dense",
        repository_id=None,
        document_id=None,
        top_k=10,
    )
