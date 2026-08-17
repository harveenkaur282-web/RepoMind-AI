from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.db.models.chunk import Chunk
from backend.app.db.models.document import Document
from backend.app.main import app
from backend.app.services.rag.service import RAGResponse

client = TestClient(app)


@pytest.mark.asyncio
async def test_query_rag_endpoint_success() -> None:
    # 1. Setup mock data
    mock_chunk = Chunk(
        id=1,
        content="This is matching test content",
        document=Document(path="tests/example.py"),
    )
    mock_rag_response = RAGResponse(
        answer="This is the LLM-generated answer.",
        chunks=[mock_chunk],
        strategy="hybrid",
        total_chunks=1,
        total_tokens=10,
    )

    # 2. Mock RAGService and VoyageEmbeddingProvider
    with (
        patch("backend.app.api.v1.endpoints.rag.RAGService") as mock_service_class,
        patch("backend.app.api.v1.endpoints.rag.VoyageEmbeddingProvider") as mock_provider_class,
    ):
        # Setup mock instances
        mock_service = MagicMock()
        mock_service.answer_query = AsyncMock(return_value=mock_rag_response)
        mock_service_class.return_value = mock_service

        mock_provider = MagicMock()
        mock_provider.embed_query = AsyncMock(return_value=[0.1] * 1024)
        mock_provider_class.return_value = mock_provider

        # 3. Call endpoint
        response = client.post(
            "/api/v1/rag/query",
            params={
                "query": "What is RepoMind?",
                "strategy": "hybrid",
                "repository_id": 42,
            },
        )

        # 4. Assertions
        assert response.status_code == 200
        payload = response.json()
        assert payload["answer"] == "This is the LLM-generated answer."
        assert payload["strategy"] == "hybrid"
        assert payload["total_chunks"] == 1
        assert len(payload["chunks"]) == 1
        assert payload["chunks"][0]["document_path"] == "tests/example.py"
        assert payload["chunks"][0]["content"] == "This is matching test content"

        # Verify underlying calls
        mock_provider.embed_query.assert_awaited_once_with("What is RepoMind?")
        mock_service.answer_query.assert_awaited_once_with(
            query="What is RepoMind?",
            query_embedding=[0.1] * 1024,
            strategy="hybrid",
            repository_id=42,
            document_id=None,
        )


@pytest.mark.asyncio
async def test_query_rag_endpoint_handles_error() -> None:
    with patch("backend.app.api.v1.endpoints.rag.RAGService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.answer_query = AsyncMock(side_effect=RuntimeError("Ollama connection failed"))
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/rag/query",
            params={
                "query": "error query",
                "strategy": "bm25",
            },
        )

        assert response.status_code == 500
        assert "Ollama connection failed" in response.json()["detail"]
