from fastapi import APIRouter

from backend.app.services.ingestion.repository_ingestor import RepositoryIngestor

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/repository")
async def ingest_repository(
    owner: str,
    repo: str,
) -> dict[str, object]:
    ingestor = RepositoryIngestor()

    processed_files = await ingestor.ingest_repository(
        owner=owner,
        repo=repo,
    )

    return {
        "repository": f"{owner}/{repo}",
        "files_processed": len(processed_files),
        "files": [{"path": file.path} for file in processed_files],
    }
