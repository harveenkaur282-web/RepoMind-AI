from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.dependencies import get_db
from backend.app.db.models.repository import Repository

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("")
async def list_repositories(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict[str, object]]:
    result = await db.execute(
        select(Repository)
        .options(selectinload(Repository.documents))
        .order_by(Repository.created_at.desc())
    )
    repositories = result.scalars().all()

    return [
        {
            "id": repository.id,
            "owner": repository.owner,
            "name": repository.name,
            "github_url": repository.github_url,
            "default_branch": repository.default_branch,
            "description": repository.description,
            "status": getattr(repository.status, "value", repository.status),
            "document_count": len(repository.documents),
            "last_ingested_at": repository.last_ingested_at.isoformat()
            if repository.last_ingested_at is not None
            else None,
            "created_at": repository.created_at.isoformat(),
            "updated_at": repository.updated_at.isoformat(),
        }
        for repository in repositories
    ]


@router.delete("/{repository_id}", status_code=204)
async def delete_repository(
    repository_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a repository and its associated documents/chunks (via cascade delete)."""
    result = await db.execute(select(Repository).where(Repository.id == repository_id))
    repository = result.scalar_one_or_none()
    if repository is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Repository not found")

    await db.delete(repository)
    await db.commit()
