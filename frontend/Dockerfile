FROM python:3.12-slim

WORKDIR /workspace

# Install dependencies using pip directly
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    streamlit \
    requests \
    pandas \
    pydantic \
    pydantic-settings \
    httpx

# Copy application files
COPY frontend/ ./frontend/

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "frontend/streamlit/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
