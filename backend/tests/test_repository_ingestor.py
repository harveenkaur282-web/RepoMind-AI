from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from backend.app.main import app
from backend.app.services.github.exceptions import GitHubNotFoundError
from backend.app.services.github.schemas import GitHubOwner, GitHubRepository
from backend.app.services.ingestion.repository_ingestor import RepositoryIngestor

client = TestClient(app)


@pytest.mark.asyncio
async def test_ingest_repository() -> None:
    github_client = AsyncMock()

    github_client.get_repository.return_value = GitHubRepository(
        id=123,
        name="RepoMind-AI",
        full_name="harveenkaur282-web/RepoMind-AI",
        owner=GitHubOwner(login="harveenkaur282-web"),
        html_url="https://github.com/harveenkaur282-web/RepoMind-AI",
        default_branch="main",
    )

    github_client.get_repository_tree.return_value = {
        "sha": "abc123",
        "tree": [],
        "truncated": False,
    }

    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    db.flush = AsyncMock()
    db.commit = AsyncMock()

    ingestor = RepositoryIngestor(db=db, github_client=github_client)

    await ingestor.ingest_repository(
        owner="harveenkaur282-web",
        repo="RepoMind-AI",
    )

    github_client.get_repository.assert_awaited_once_with(
        owner="harveenkaur282-web",
        repo="RepoMind-AI",
    )

    github_client.get_repository_tree.assert_awaited_once_with(
        owner="harveenkaur282-web",
        repo="RepoMind-AI",
        tree_sha="main",
        recursive=True,
    )

    db.flush.assert_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingest_repository_persists_repository_and_documents() -> None:
    github_client = AsyncMock()
    github_client.get_repository.return_value = GitHubRepository(
        id=123,
        name="RepoMind-AI",
        full_name="harveenkaur282-web/RepoMind-AI",
        owner=GitHubOwner(login="harveenkaur282-web"),
        html_url="https://github.com/harveenkaur282-web/RepoMind-AI",
        default_branch="main",
        description="Repository for AI metadata ingestion",
    )
    github_client.get_repository_tree.return_value = {
        "sha": "abc123",
        "tree": [
            {"type": "blob", "path": "README.md", "size": 100},
            {"type": "blob", "path": "backend/app.py", "size": 125},
            {"type": "dir", "path": "docs"},
        ],
        "truncated": False,
    }
    github_client.get_file_content.side_effect = ["# RepoMind AI\n", "print('hello')\n"]

    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()

    ingestor = RepositoryIngestor(db=db, github_client=github_client)

    processed_files = await ingestor.ingest_repository(
        owner="harveenkaur282-web",
        repo="RepoMind-AI",
    )

    assert len(processed_files) == 2
    assert db.add.call_count >= 3
    db.flush.assert_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingest_repository_endpoint_handles_duplicate_ingestion() -> None:
    with patch(
        "backend.app.api.v1.endpoints.ingestion.RepositoryIngestor.ingest_repository",
        new=AsyncMock(side_effect=IntegrityError("duplicate key", None, None)),
    ):
        response = client.post(
            "/api/v1/ingestion/repository",
            params={"owner": "example", "repo": "project"},
        )

    assert response.status_code == 409
    assert "already been ingested" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ingest_repository_endpoint_handles_missing_github_repository() -> None:
    with patch(
        "backend.app.api.v1.endpoints.ingestion.RepositoryIngestor.ingest_repository",
        new=AsyncMock(side_effect=GitHubNotFoundError("Repository not found: example/project")),
    ):
        response = client.post(
            "/api/v1/ingestion/repository",
            params={"owner": "example", "repo": "project"},
        )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ingest_repository_endpoint_instantiates_embedding_service() -> None:
    with patch("backend.app.api.v1.endpoints.ingestion.RepositoryIngestor") as mock_ingestor_class:
        mock_ingestor = MagicMock()
        mock_ingestor.ingest_repository = AsyncMock(return_value=[])
        mock_ingestor_class.return_value = mock_ingestor

        response = client.post(
            "/api/v1/ingestion/repository",
            params={"owner": "example", "repo": "project"},
        )

        assert response.status_code == 200
        mock_ingestor_class.assert_called_once()
        kwargs = mock_ingestor_class.call_args[1]
        assert "embedding_service" in kwargs
        assert kwargs["embedding_service"] is not None


@pytest.mark.asyncio
async def test_update_repository_endpoint_success() -> None:
    with patch("backend.app.api.v1.endpoints.ingestion.RepositoryIngestor") as mock_ingestor_class:
        mock_ingestor = MagicMock()
        mock_ingestor.update_repository = AsyncMock(return_value=[])
        mock_ingestor_class.return_value = mock_ingestor

        response = client.post(
            "/api/v1/ingestion/repository/1/update",
        )

        assert response.status_code == 200
        mock_ingestor_class.assert_called_once()
        mock_ingestor.update_repository.assert_awaited_once_with(repository_id=1)
