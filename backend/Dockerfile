FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace

# Install dependencies using uv
COPY pyproject.toml ./
RUN uv pip install --system \
    fastapi \
    uvicorn \
    pydantic \
    pydantic-settings \
    sqlalchemy \
    asyncpg \
    pgvector \
    alembic \
    redis \
    structlog \
    voyageai \
    onnxruntime \
    tokenizers \
    huggingface_hub \
    numpy \
    httpx

# Copy application files
COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY evaluation/ ./evaluation/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]
