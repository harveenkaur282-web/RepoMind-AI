import hashlib
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.document import Document
from backend.app.db.models.repository import Repository, RepositoryStatus
from backend.app.services.github.client import GitHubClient
from backend.app.services.ingestion.file_filter import should_ingest_file
from backend.app.services.ingestion.schemas import ProcessedFile


class RepositoryIngestor:
    def __init__(
        self,
        db: AsyncSession | None = None,
        github_client: GitHubClient | None = None,
    ) -> None:
        self.db = db
        self.github_client = github_client or GitHubClient()

    async def ingest_repository(
        self,
        owner: str,
        repo: str,
    ) -> list[ProcessedFile]:
        if self.db is None:
            raise ValueError("Database session is required for repository ingestion.")

        repository = await self.github_client.get_repository(
            owner=owner,
            repo=repo,
        )

        db_repository = Repository(
            github_url=repository.html_url,
            owner=repository.owner.login,
            name=repository.name,
            default_branch=repository.default_branch,
            description=repository.description,
            status=RepositoryStatus.INGESTING,
        )

        self.db.add(db_repository)
        await self.db.flush()

        tree_response = await self.github_client.get_repository_tree(
            owner=owner,
            repo=repo,
            tree_sha=repository.default_branch,
            recursive=True,
        )

        processed_files: list[ProcessedFile] = []
        tree_entries: list[dict[str, Any]] = tree_response.get("tree", [])
        if tree_response.get("truncated", False):
            raise RuntimeError("Repository tree is truncated; ingestion is incomplete.")

        for entry in tree_entries:
            if entry.get("type") != "blob":
                continue

            path = entry.get("path")
            size = entry.get("size")

            if not should_ingest_file(path, file_size=size):
                continue

            try:
                content = await self.github_client.get_file_content(
                    owner=owner,
                    repo=repo,
                    path=path,
                )
                document = Document(
                    repository_id=db_repository.id,
                    document_type="code",
                    path=path,
                    title=path.split("/")[-1],
                    content=content,
                    source_url=f"https://github.com/{owner}/{repo}/blob/{repository.default_branch}/{path}",
                    content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                )

                self.db.add(document)
                processed_files.append(ProcessedFile(path=path, content=content))
            except Exception as exc:
                print(f"Error processing file {path}: {exc}")
                continue

        db_repository.status = RepositoryStatus.READY
        db_repository.last_ingested_at = datetime.now(UTC)

        await self.db.flush()
        await self.db.commit()

        return processed_files
