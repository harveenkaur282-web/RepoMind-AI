import hashlib
import inspect
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.chunk import Chunk
from backend.app.db.models.document import Document
from backend.app.db.models.repository import Repository, RepositoryStatus
from backend.app.services.chunking.factory import ChunkerFactory
from backend.app.services.embeddings.service import EmbeddingService
from backend.app.services.github.client import GitHubClient
from backend.app.services.ingestion.file_filter import should_ingest_file
from backend.app.services.ingestion.schemas import ProcessedFile


class RepositoryIngestor:
    def __init__(
        self,
        db: AsyncSession | None = None,
        github_client: GitHubClient | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.db = db
        self.github_client = github_client or GitHubClient()
        self.embedding_service = embedding_service

    async def ingest_repository(
        self,
        owner: str,
        repo: str,
    ) -> list[ProcessedFile]:
        if self.db is None:
            raise ValueError("Database session is required for repository ingestion.")

        github_url = f"https://github.com/{owner}/{repo}"

        existing_result = self.db.execute(
            select(Repository).where(Repository.github_url == github_url)
        )

        if inspect.isawaitable(existing_result):
            existing_result = await existing_result

        if existing_result.scalar_one_or_none() is not None:
            raise ValueError(f"Repository has already been ingested: {github_url}")

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

        chunker = ChunkerFactory.get("document_aware")

        for entry in tree_entries:
            if entry.get("type") != "blob":
                continue

            path = entry.get("path")
            size = entry.get("size")

            if not path or not should_ingest_file(path, file_size=size):
                continue

            try:
                content = await self.github_client.get_file_content(
                    owner=owner,
                    repo=repo,
                    path=path,
                )

                suffix = Path(path).suffix.lower()

                if suffix in {".md", ".markdown", ".mdx"}:
                    document_type = "markdown"
                elif suffix in {
                    ".py",
                    ".js",
                    ".jsx",
                    ".ts",
                    ".tsx",
                    ".java",
                    ".cpp",
                    ".c",
                    ".h",
                    ".hpp",
                    ".go",
                    ".rs",
                    ".rb",
                    ".php",
                    ".cs",
                    ".swift",
                    ".kt",
                }:
                    document_type = "code"
                else:
                    document_type = "text"

                document = Document(
                    repository_id=db_repository.id,
                    document_type=document_type,
                    path=path,
                    title=path.split("/")[-1],
                    content=content,
                    source_url=(
                        f"https://github.com/{owner}/{repo}/blob/{repository.default_branch}/{path}"
                    ),
                    content_hash=entry.get("sha")
                    or hashlib.sha256(content.encode("utf-8")).hexdigest(),
                )

                self.db.add(document)

                # Flush so the Document receives its database ID.
                await self.db.flush()

                chunk_results = chunker.chunk_document(document)

                for chunk_result in chunk_results:
                    chunk = Chunk(
                        document_id=document.id,
                        content=chunk_result.text,
                        chunk_index=chunk_result.chunk_index,
                        start_char=chunk_result.start_char,
                        end_char=chunk_result.end_char,
                        strategy="document_aware",
                        metadata_json=json.dumps(chunk_result.metadata),
                    )

                    self.db.add(chunk)

                processed_files.append(
                    ProcessedFile(
                        path=path,
                        content=content,
                    )
                )

            except Exception as exc:
                print(f"Error processing file {path}: {exc}")
                continue

        # Flush all newly created chunks before the embedding service queries them.
        await self.db.flush()

        if self.embedding_service is not None:
            await self.embedding_service.embed_chunks(
                repository_id=db_repository.id,
            )

        db_repository.status = RepositoryStatus.READY
        db_repository.last_ingested_at = datetime.now(UTC)

        await self.db.flush()
        await self.db.commit()

        return processed_files

    async def update_repository(
        self,
        repository_id: int,
    ) -> list[ProcessedFile]:
        """Incrementally sync/update repository documents and chunks using remote SHA checks."""
        if self.db is None:
            raise ValueError("Database session is required for repository update.")

        # 1. Fetch existing repository
        result = await self.db.execute(select(Repository).where(Repository.id == repository_id))
        db_repository = result.scalar_one_or_none()
        if db_repository is None:
            raise ValueError(f"Repository not found: {repository_id}")

        owner = db_repository.owner
        repo = db_repository.name

        db_repository.status = RepositoryStatus.INGESTING
        await self.db.flush()

        try:
            # 2. Fetch existing documents
            doc_result = await self.db.execute(
                select(Document).where(Document.repository_id == repository_id)
            )
            db_documents = {doc.path: doc for doc in doc_result.scalars().all()}

            # 3. Fetch remote files and default branch
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

            tree_entries: list[dict[str, Any]] = tree_response.get("tree", [])
            if tree_response.get("truncated", False):
                raise RuntimeError("Repository tree is truncated; update is incomplete.")

            # Create remote file lookup
            remote_files = {}
            for entry in tree_entries:
                if entry.get("type") == "blob":
                    path = entry.get("path")
                    if path:
                        remote_files[path] = entry

            # Delete files that no longer exist remotely
            deleted_paths = []
            for db_path, db_doc in db_documents.items():
                if db_path not in remote_files:
                    deleted_paths.append(db_path)
                    await self.db.delete(db_doc)

            chunker = ChunkerFactory.get("document_aware")
            processed_files: list[ProcessedFile] = []
            new_chunks_added = False

            # Ingest new or modified files
            for entry in tree_entries:
                if entry.get("type") != "blob":
                    continue

                path = entry.get("path")
                size = entry.get("size")
                remote_sha = entry.get("sha")

                if not path or not should_ingest_file(path, file_size=size):
                    continue

                existing_doc = db_documents.get(path)

                # Skip if file is unchanged (SHA matches)
                if existing_doc and existing_doc.content_hash == remote_sha:
                    continue

                # If file exists but SHA differs, delete old record first (cascades chunk deletions)
                if existing_doc:
                    await self.db.delete(existing_doc)
                    await self.db.flush()

                try:
                    content = await self.github_client.get_file_content(
                        owner=owner,
                        repo=repo,
                        path=path,
                    )

                    suffix = Path(path).suffix.lower()
                    if suffix in {".md", ".markdown", ".mdx"}:
                        document_type = "markdown"
                    elif suffix in {
                        ".py",
                        ".js",
                        ".jsx",
                        ".ts",
                        ".tsx",
                        ".go",
                        ".rs",
                        ".java",
                        ".cpp",
                        ".c",
                        ".h",
                        ".cs",
                        ".rb",
                        ".php",
                        ".html",
                        ".css",
                        ".sh",
                        ".yml",
                        ".yaml",
                        ".kt",
                    }:
                        document_type = "code"
                    else:
                        document_type = "text"

                    document = Document(
                        repository_id=db_repository.id,
                        document_type=document_type,
                        path=path,
                        title=path.split("/")[-1],
                        content=content,
                        source_url=(
                            f"https://github.com/{owner}/{repo}/blob/{repository.default_branch}/{path}"
                        ),
                        content_hash=remote_sha
                        or hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    )

                    self.db.add(document)
                    await self.db.flush()

                    chunk_results = chunker.chunk_document(document)
                    for chunk_result in chunk_results:
                        chunk = Chunk(
                            document_id=document.id,
                            content=chunk_result.text,
                            chunk_index=chunk_result.chunk_index,
                            start_char=chunk_result.start_char,
                            end_char=chunk_result.end_char,
                            strategy="document_aware",
                            metadata_json=json.dumps(chunk_result.metadata),
                        )
                        self.db.add(chunk)
                        new_chunks_added = True

                    processed_files.append(
                        ProcessedFile(
                            path=path,
                            content=content,
                        )
                    )

                except Exception as exc:
                    print(f"Error updating file {path}: {exc}")
                    continue

            # Flush new chunks and generate embeddings if needed
            await self.db.flush()

            if new_chunks_added and self.embedding_service is not None:
                await self.embedding_service.embed_chunks(
                    repository_id=db_repository.id,
                )

            db_repository.status = RepositoryStatus.READY
            db_repository.last_ingested_at = datetime.now(UTC)

            await self.db.flush()
            await self.db.commit()

            return processed_files

        except Exception as exc:
            db_repository.status = RepositoryStatus.FAILED
            await self.db.flush()
            await self.db.commit()
            raise exc
