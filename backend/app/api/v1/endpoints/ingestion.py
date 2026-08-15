from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.dependencies import get_db
from backend.app.services.github.exceptions import (
    GitHubAPIError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)
from backend.app.services.ingestion.repository_ingestor import RepositoryIngestor

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/repository")
async def ingest_repository(
    owner: str,
    repo: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    ingestor = RepositoryIngestor(db=db)

    try:
        processed_files = await ingestor.ingest_repository(
            owner=owner,
            repo=repo,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GitHubNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GitHubRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except GitHubAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Repository has already been ingested.",
        ) from exc

    return {
        "repository": f"{owner}/{repo}",
        "files_processed": len(processed_files),
        "files": [{"path": file.path} for file in processed_files],
    }
