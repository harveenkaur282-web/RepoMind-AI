from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.dependencies import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "RepoMind AI API",
        "version": "0.1.0",
    }


@router.get("/health/diagnostics")
async def get_diagnostics(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    from sqlalchemy import func

    from backend.app.db.models.chunk import Chunk
    from backend.app.db.models.document import Document
    from backend.app.db.models.repository import Repository

    repo_count = await db.scalar(select(func.count(Repository.id)))
    doc_count = await db.scalar(select(func.count(Document.id)))
    chunk_count = await db.scalar(select(func.count(Chunk.id)))

    repo_result = await db.execute(select(Repository))
    repos = repo_result.scalars().all()
    repo_details = []
    for r in repos:
        doc_c = await db.scalar(
            select(func.count(Document.id)).where(Document.repository_id == r.id)
        )
        chunk_c = await db.scalar(
            select(func.count(Chunk.id)).join(Document).where(Document.repository_id == r.id)
        )
        repo_details.append(
            {
                "id": r.id,
                "owner": r.owner,
                "name": r.name,
                "document_count": doc_c,
                "chunk_count": chunk_c,
            }
        )

    return {
        "repository_count": repo_count or 0,
        "document_count": doc_count or 0,
        "chunk_count": chunk_count or 0,
        "repositories": repo_details,
    }
