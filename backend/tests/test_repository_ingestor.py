from unittest.mock import AsyncMock

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

    ingestor = RepositoryIngestor(github_client=github_client)

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
