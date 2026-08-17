import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.chunk import Chunk
from backend.app.db.models.document import Document
from backend.app.db.models.repository import Repository, RepositoryStatus
from backend.app.db.session import AsyncSessionLocal, engine
from backend.app.services.retrieval.service import RetrievalService


def make_vector(index: int) -> list[float]:
    vector = [0.0] * 768
    vector[index] = 1.0
    return vector


@pytest_asyncio.fixture
async def retrieval_db() -> AsyncSession:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    async with AsyncSessionLocal() as session:
        yield session

        await session.rollback()

        await session.execute(
            text(
                """
                DELETE FROM chunks
                WHERE document_id IN (
                    SELECT id
                    FROM documents
                    WHERE path LIKE 'integration-test/%'
                )
                """
            )
        )

        await session.execute(
            text(
                """
                DELETE FROM documents
                WHERE path LIKE 'integration-test/%'
                """
            )
        )

        await session.execute(
            text(
                """
                DELETE FROM repositories
                WHERE github_url = 'https://github.com/test/retrieval-integration'
                """
            )
        )

        await session.commit()


@pytest.mark.asyncio
async def test_retrieval_returns_nearest_chunks(
    retrieval_db: AsyncSession,
) -> None:
    repository = Repository(
        github_url="https://github.com/test/retrieval-integration",
        owner="test",
        name="retrieval-integration",
        default_branch="main",
        description="pgvector integration test",
        status=RepositoryStatus.READY,
    )

    retrieval_db.add(repository)
    await retrieval_db.flush()

    document = Document(
        repository_id=repository.id,
        document_type="code",
        path="integration-test/example.py",
        title="example.py",
        content="integration test document",
        source_url="https://github.com/test/retrieval-integration/blob/main/example.py",
        content_hash="integration-test-hash",
    )

    retrieval_db.add(document)
    await retrieval_db.flush()

    query_vector = make_vector(0)

    nearest_chunk = Chunk(
        document_id=document.id,
        content="def retrieve_user(): return user",
        chunk_index=0,
        start_char=0,
        end_char=35,
        strategy="document_aware",
        local_embedding=make_vector(0),
    )

    second_chunk = Chunk(
        document_id=document.id,
        content="def create_order(): return order",
        chunk_index=1,
        start_char=36,
        end_char=70,
        strategy="document_aware",
        local_embedding=make_vector(1),
    )

    third_chunk = Chunk(
        document_id=document.id,
        content="class PaymentService: pass",
        chunk_index=2,
        start_char=71,
        end_char=100,
        strategy="document_aware",
        local_embedding=make_vector(2),
    )

    retrieval_db.add_all(
        [
            nearest_chunk,
            second_chunk,
            third_chunk,
        ]
    )

    await retrieval_db.commit()

    service = RetrievalService(retrieval_db)

    results = await service.search(
        query_embedding=query_vector,
        top_k=3,
    )

    assert len(results) == 3

    assert results[0].chunk.content == "def retrieve_user(): return user"
    assert results[1].chunk.content == "def create_order(): return order"
    assert results[2].chunk.content == "class PaymentService: pass"
