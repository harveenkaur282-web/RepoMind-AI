from unittest.mock import MagicMock, patch

import pytest

from backend.app.services.embeddings.voyage import VoyageEmbeddingProvider


def test_voyage_provider_metadata() -> None:
    provider = VoyageEmbeddingProvider()

    assert provider.model_name == "voyage-code-3"
    assert provider.dimensions == 1024


@pytest.mark.asyncio
async def test_voyage_embed_documents() -> None:
    mock_result = MagicMock()
    mock_result.embeddings = [
        [0.1] * 1024,
        [0.2] * 1024,
    ]

    with patch("backend.app.services.embeddings.voyage.voyageai.Client") as mock_client:
        mock_client.return_value.embed.return_value = mock_result

        provider = VoyageEmbeddingProvider()

        embeddings = await provider.embed_documents(
            [
                "def hello(): return 'hello'",
                "class User: pass",
            ]
        )

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1024
        assert len(embeddings[1]) == 1024

        mock_client.return_value.embed.assert_called_once_with(
            [
                "def hello(): return 'hello'",
                "class User: pass",
            ],
            model="voyage-code-3",
            input_type="document",
        )


@pytest.mark.asyncio
async def test_voyage_embed_query() -> None:
    mock_result = MagicMock()
    mock_result.embeddings = [[0.3] * 1024]

    with patch("backend.app.services.embeddings.voyage.voyageai.Client") as mock_client:
        mock_client.return_value.embed.return_value = mock_result

        provider = VoyageEmbeddingProvider()

        embedding = await provider.embed_query("Where is the User class defined?")

        assert len(embedding) == 1024

        mock_client.return_value.embed.assert_called_once_with(
            ["Where is the User class defined?"],
            model="voyage-code-3",
            input_type="query",
        )
