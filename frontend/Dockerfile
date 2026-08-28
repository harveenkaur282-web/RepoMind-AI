FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace

# Install dependencies using uv
COPY pyproject.toml ./
RUN uv pip install --system \
    streamlit \
    requests \
    pandas \
    pydantic \
    pydantic-settings \
    httpx

# Copy application files
COPY frontend/ ./frontend/

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "frontend/streamlit/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
