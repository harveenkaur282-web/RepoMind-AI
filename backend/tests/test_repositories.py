from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.api.v1.endpoints.repositories import list_repositories
from backend.app.db.models.repository import Repository, RepositoryStatus


@pytest.mark.asyncio
async def test_list_repositories_returns_repository_summaries() -> None:
    db = AsyncMock()

    repository = Repository(
        id=1,
        github_url="https://github.com/example/project",
        owner="example",
        name="project",
        default_branch="main",
        description="Demo project",
        status=RepositoryStatus.READY,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repository.documents = []

    result = MagicMock()
    result.scalars.return_value.all.return_value = [repository]
    db.execute.return_value = result

    repositories = await list_repositories(db=db)

    assert len(repositories) == 1
    assert repositories[0]["owner"] == "example"
    assert repositories[0]["name"] == "project"
    assert repositories[0]["status"] == "ready"
    assert repositories[0]["document_count"] == 0
