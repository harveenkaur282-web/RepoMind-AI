from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.api.v1.endpoints.repositories import delete_repository, list_repositories
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


@pytest.mark.asyncio
async def test_delete_repository_success() -> None:
    db = AsyncMock()
    repo = Repository(id=1, owner="test", name="repo")

    # Mock DB query
    result = MagicMock()
    result.scalar_one_or_none.return_value = repo
    db.execute.return_value = result

    await delete_repository(repository_id=1, db=db)

    db.delete.assert_called_once_with(repo)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_repository_not_found() -> None:
    db = AsyncMock()

    # Mock DB query returning None
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await delete_repository(repository_id=99, db=db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Repository not found"
    db.delete.assert_not_called()
    db.commit.assert_not_awaited()
