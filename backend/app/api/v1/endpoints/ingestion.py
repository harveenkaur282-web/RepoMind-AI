from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.dependencies import get_db
from backend.app.services.ingestion.repository_ingestor import RepositoryIngestor

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/repository")
async def ingest_repository(
    owner: str,
    repo: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    ingestor = RepositoryIngestor(db=db)

    processed_files = await ingestor.ingest_repository(
        owner=owner,
        repo=repo,
    )

    return {
        "repository": f"{owner}/{repo}",
        "files_processed": len(processed_files),
        "files": [{"path": file.path} for file in processed_files],
    }
