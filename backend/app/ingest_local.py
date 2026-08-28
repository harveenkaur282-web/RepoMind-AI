from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, select

from backend.app.db.models.chunk import Chunk
from backend.app.db.models.document import Document
from backend.app.db.models.repository import Repository, RepositoryStatus
from backend.app.db.session import AsyncSessionLocal
from backend.app.services.chunking.factory import ChunkerFactory
from backend.app.services.embeddings.local import LocalEmbeddingProvider
from backend.app.services.embeddings.service import EmbeddingService
from backend.app.services.ingestion.file_filter import should_ingest_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_local")


async def ingest_local_repo(
    repo_dir: Path,
    owner: str = "harveenkaur282-web",
    repo_name: str = "RepoMind-AI",
) -> None:
    logger.info("Starting clean local ingestion for %s/%s from %s", owner, repo_name, repo_dir)

    async with AsyncSessionLocal() as session:
        # 1. Clean wipe existing repo if present using fast batch delete statements
        stmt = select(Repository).where(
            Repository.owner == owner,
            Repository.name == repo_name,
        )
        res = await session.execute(stmt)
        existing_repo = res.scalar_one_or_none()

        if existing_repo is not None:
            logger.info(
                "Found existing repository (id=%d). Wiping old chunks and documents...",
                existing_repo.id,
            )
            doc_ids = (
                (
                    await session.execute(
                        select(Document.id).where(Document.repository_id == existing_repo.id)
                    )
                )
                .scalars()
                .all()
            )
            if doc_ids:
                await session.execute(delete(Chunk).where(Chunk.document_id.in_(doc_ids)))
                await session.commit()
                await session.execute(
                    delete(Document).where(Document.repository_id == existing_repo.id)
                )
                await session.commit()
            await session.delete(existing_repo)
            await session.commit()

        # 2. Create fresh Repository record
        db_repository = Repository(
            github_url=f"https://github.com/{owner}/{repo_name}",
            owner=owner,
            name=repo_name,
            default_branch="main",
            description="RepoMind-AI code intelligence platform",
            status=RepositoryStatus.INGESTING,
        )
        session.add(db_repository)
        await session.commit()
        await session.refresh(db_repository)
        logger.info("Created repository record with ID: %d", db_repository.id)

        # 3. Walk local files
        chunker = ChunkerFactory.get("document_aware")
        processed_files_count = 0
        total_chunks_count = 0

        # Recursively scan repository
        for file_path in repo_dir.rglob("*"):
            if not file_path.is_file():
                continue

            rel_path = file_path.relative_to(repo_dir).as_posix()

            # Ignore virtual environments, git data, caches, build artifacts
            parts = rel_path.split("/")
            if any(
                p.startswith(".")
                or p in {"venv", ".venv", "__pycache__", "node_modules", "dist", "build"}
                for p in parts[:-1]
            ):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue  # Skip binary files

            if not should_ingest_file(rel_path, file_size=len(content.encode("utf-8"))):
                continue

            suffix = file_path.suffix.lower()
            if suffix in {".md", ".markdown", ".mdx"}:
                doc_type = "markdown"
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
            }:
                doc_type = "code"
            else:
                doc_type = "text"

            doc = Document(
                repository_id=db_repository.id,
                document_type=doc_type,
                path=rel_path,
                title=file_path.name,
                content=content,
                source_url=f"https://github.com/{owner}/{repo_name}/blob/main/{rel_path}",
                content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            )
            session.add(doc)
            await session.flush()

            chunk_results = chunker.chunk_document(doc)
            for chunk_res in chunk_results:
                chunk = Chunk(
                    document_id=doc.id,
                    content=chunk_res.text,
                    chunk_index=chunk_res.chunk_index,
                    start_char=chunk_res.start_char,
                    end_char=chunk_res.end_char,
                    strategy="document_aware",
                    metadata_json=json.dumps(chunk_res.metadata),
                )
                session.add(chunk)
                total_chunks_count += 1

            processed_files_count += 1
            if processed_files_count % 10 == 0:
                await session.commit()
                logger.info(
                    "Processed %d files (%d chunks total)...",
                    processed_files_count,
                    total_chunks_count,
                )

        await session.commit()
        logger.info(
            "Finished document ingestion: %d files, %d chunks saved.",
            processed_files_count,
            total_chunks_count,
        )

        # 4. Generate local ONNX embeddings
        logger.info("Generating local ONNX embeddings for %d chunks...", total_chunks_count)
        provider = LocalEmbeddingProvider()
        embedding_service = EmbeddingService(db=session, provider=provider, batch_size=32)

        embedded_count = await embedding_service.embed_chunks(repository_id=db_repository.id)
        logger.info("Successfully generated embeddings for %d chunks!", embedded_count)

        # 5. Mark repository READY
        db_repository.status = RepositoryStatus.READY
        db_repository.last_ingested_at = datetime.now(UTC)
        await session.merge(db_repository)
        await session.commit()

        logger.info("Clean ingestion complete! Repository %s/%s is READY.", owner, repo_name)


if __name__ == "__main__":
    repo_path = Path(__file__).resolve().parents[2]
    asyncio.run(ingest_local_repo(repo_path))
