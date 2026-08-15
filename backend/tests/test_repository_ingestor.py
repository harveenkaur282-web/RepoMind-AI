from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.services.github.schemas import GitHubOwner, GitHubRepository
from backend.app.services.ingestion.repository_ingestor import RepositoryIngestor


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
