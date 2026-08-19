# RepoMind-AI

An Intelligent RAG-powered Codebase Search and Question-Answering Workspace for GitHub Repositories.

## Reproducibility Guide

You can run **RepoMind-AI** fully local and containerized. The guide below covers running everything via a single Docker command, utilizing a **local native ONNX embedding model** (completely free, no API key required) and connecting to your local **Ollama** server.

### Prerequisites
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (must be open and running on your host machine)
*   [Ollama](https://ollama.com/) (running on your host machine)
*   [Python 3.12+](https://www.python.org/downloads/) (for running local scripts or tests, optional)

---

### Step-by-Step Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/harveenkaur282-web/RepoMind-AI.git
    cd RepoMind-AI
    ```

2.  **Configure Environment Variables**
    Create a `.env` file in the project root:
    ```env
    APP_NAME=RepoMind AI
    ENVIRONMENT=development
    DEBUG=true

    # Database URLs (When running in Docker, Postgres is reachable at the host name 'postgres')
    DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/repomind
    REDIS_URL=redis://redis:6379/0

    # LLM configuration (Queries are routed back to your host machine's Ollama instance)
    LLM_PROVIDER=ollama
    OLLAMA_URL=http://host.docker.internal:11434
    OLLAMA_MODEL=qwen2.5-coder:7b

    # Required for private repos or higher GitHub API rate limits
    GITHUB_TOKEN=your_github_token_here
    ```

3.  **Prepare the Local Embedding Model**
    Before spinning up Docker, download the weights for our local, native ONNX embedding model (`Xenova/all-mpnet-base-v2`, 768 dimensions) by running:
    ```bash
    uv run python backend/app/download_model.py
    ```

4.  **Spin up the entire stack**
    Run the following command to build the backend/frontend containers and start Postgres, Redis, Grafana, Streamlit, and FastAPI together:
    ```bash
    docker compose up --build -d
    ```

5.  **Run Database Migrations**
    Run the Alembic schema updates inside the running backend container:
    ```bash
    docker compose exec backend uv run alembic upgrade head
    ```

6.  **Pull the Ollama LLM Model**
    Make sure your local Ollama application is running on your host computer, then pull the model:
    ```bash
    ollama pull qwen2.5-coder:7b
    ```

7.  **Access the Application**
    *   **Frontend Streamlit UI**: `http://localhost:8501`
    *   **FastAPI Backend Server**: `http://localhost:8000`
    *   **Grafana Monitoring**: `http://localhost:3000` (credentials: `admin`/`admin`)

---

## Main Features

*   **Repository Ingestion**: Ingest any repository directly by inputting `owner/name`. Supports custom chunking strategies.
*   **Local ONNX Embedding Generation**: Runs embeddings locally via ONNX Runtime using Xenova's `all-mpnet-base-v2` model. Completely offline, fast, and free.
*   **Incremental Repository Updates**: Uses Git blob SHA comparisons to sync remote files. It skips unchanged documents to avoid redundant chunking and embedding, processes modified/new files, and cleans up deleted documents.
*   **Hybrid Search with RRF**: Offers semantic vector similarity matching, BM25 sparse keyword matching, and Hybrid Reciprocal Rank Fusion (RRF) search.
*   **Local LLM Generation**: Routes queries to your host Ollama server (defaulting to `qwen2.5-coder:7b`) to maintain code privacy.
*   **Developer Diagnostics**: Inspect database row metrics, test model latencies, and compare retrieval strategies side-by-side.

---

## Tech Stack

*   **Frontend**: Streamlit
*   **Backend**: FastAPI (Python 3.12)
*   **ORM**: SQLAlchemy (Async Engine)
*   **Database**: PostgreSQL with `pgvector`
*   **Local Embeddings**: ONNX Runtime (`Xenova/all-mpnet-base-v2`, 768 dimensions)
*   **Local LLM**: Ollama (`qwen2.5-coder:7b`)
*   **Migrations**: Alembic
*   **Linter/Formatter**: Ruff
