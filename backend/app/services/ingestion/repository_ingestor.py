from typing import Any

from backend.app.services.github.client import GitHubClient
from backend.app.services.ingestion.file_filter import should_ingest_file
from backend.app.services.ingestion.schemas import ProcessedFile


class RepositoryIngestor:
    def __init__(self, github_client: GitHubClient | None = None) -> None:
        self.github_client = github_client or GitHubClient()

    async def ingest_repository(
        self,
        owner: str,
        repo: str,
    ) -> list[ProcessedFile]:

        repository = await self.github_client.get_repository(
            owner=owner,
            repo=repo,
        )

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
                processed_files.append(ProcessedFile(path=path, content=content))
            except Exception as e:
                print(f"Error processing file {path}: {e}")
                continue

        return processed_files
