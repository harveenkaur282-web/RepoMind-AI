from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.services.rag.prompts import PROMPT_STRATEGIES, get_system_prompt
from backend.app.services.rag.service import RAGService


def test_prompt_strategies_exist() -> None:
    # Verify exactly three strategies exist
    assert len(PROMPT_STRATEGIES) == 3
    assert "concise_grounded" in PROMPT_STRATEGIES
    assert "detailed_grounded" in PROMPT_STRATEGIES
    assert "developer_assistant" in PROMPT_STRATEGIES


def test_prompt_strategies_content() -> None:
    # Verify that each produces the expected system prompt structures
    assert "Be concise and do not invent information." in get_system_prompt("concise_grounded")
    assert (
        "explicitly say when the context is insufficient"
        in get_system_prompt("detailed_grounded").lower()
    )
    assert (
        "senior developer helping understand the repository"
        in get_system_prompt("developer_assistant").lower()
    )


def test_invalid_strategy_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Invalid prompt strategy"):
        get_system_prompt("invalid_strategy")


@pytest.mark.asyncio
async def test_rag_service_injects_prompt_correctly() -> None:
    mock_retrieval = MagicMock()
    mock_retrieval.search = AsyncMock(return_value=[])

    mock_assembler = MagicMock()
    mock_assembler.assemble = MagicMock()
    mock_assembler.assemble.return_value.context_str = "Clean codebase chunks"
    mock_assembler.assemble.return_value.chunks = []
    mock_assembler.assemble.return_value.total_chunks = 0
    mock_assembler.assemble.return_value.total_tokens = 0

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="LLM explanation output")

    rag_service = RAGService(
        retrieval_service=mock_retrieval,
        context_assembler=mock_assembler,
        llm_provider=mock_llm,
    )

    response = await rag_service.answer_query(
        query="Explain main.py",
        system_prompt="Acting as a senior developer...",
        prompt_strategy="developer_assistant",
    )

    assert response.answer == "LLM explanation output"
    assert response.prompt_strategy == "developer_assistant"

    # Verify query and context are passed exactly without modifications
    mock_llm.generate.assert_awaited_once_with(
        context="Clean codebase chunks",
        query="Explain main.py",
        system_prompt="Acting as a senior developer...",
    )
