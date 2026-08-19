FROM python:3.12-slim

WORKDIR /workspace

# Install dependencies using pip directly, ignoring torch
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
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

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
