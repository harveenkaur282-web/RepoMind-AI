import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import AsyncSessionLocal, engine


@pytest_asyncio.fixture
async def retrieval_db() -> AsyncSession:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    async with AsyncSessionLocal() as session:
        yield session

        await session.rollback()
