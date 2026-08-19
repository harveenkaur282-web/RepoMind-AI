FROM python:3.12-slim

COPY --from=astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace

# Install dependencies using uv cache
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-package torch --no-dev

# Copy application files
COPY frontend/ ./frontend/

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "frontend/streamlit/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
