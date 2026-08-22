# RepoMind-AI

> [!IMPORTANT]
> **Please refer to the latest commit on the `main` branch for the most up-to-date documentation and code changes.**

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

    # LLM configuration (Queries are routed to Groq Cloud API for fast completions)
    LLM_PROVIDER=groq
    GROQ_API_KEY=your_groq_api_key_here
    GROQ_MODEL=openai/gpt-oss-20b

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

## Codebase Architecture

The project is structured logically separating the backend API service, frontend Streamlit dashboards, and migration schema management:

```
├── alembic/                      # Alembic migration environment scripts and revisions
├── backend/
│   ├── Dockerfile                # Production pip-based minimal containerizer for FastAPI
│   └── app/
├── screenshots/                  # Folder containing user-interface execution screenshots

│       ├── api/                  # FastAPI router mappings and endpoint handlers (v1)
│       ├── core/                 # App configurations (Pydantic base settings) and db connections
│       ├── db/                   # SQLAlchemy declarative model schemas (Chunk, Document, Feedback)
│       ├── evaluation/           # RAG retrieval evaluation scripts and datasets
│       ├── monitoring/           # Prometheus metrics tracking & structured logger configuration
│       └── services/
│           ├── chunking/         # Code parsers (recursive and document-aware chunking strategies)
│           ├── embeddings/       # local ONNX model runtime & Voyage client interfaces
│           ├── generation/       # Chat completion client providers (Ollama, Groq, OpenRouter)
│           └── retrieval/        # BM25 sparse keyword & pgvector dense semantic search implementations
├── frontend/
│   ├── Dockerfile                # Streamlit dashboard container configuration
│   └── streamlit/
│       └── app.py                # User interface and diagnostics pages
├── docker-compose.yml            # Multi-container service orchestrator
└── pyproject.toml                # Project dependencies and workspace configurations
```

---

## Tech Stack & Core Libraries

*   **Application Services**:
    *   **FastAPI**: Python async framework powering the backend REST endpoints. Utilizes lifespan event managers for startup pre-loading optimizations.
    *   **Streamlit**: Frontend user dashboard providing ingestion triggers, assistant dialog components, and developer statistics.
*   **Database & Vector Engine**:
    *   **PostgreSQL**: Primary datastore configured with the **`pgvector`** extension to handle 768-dimension vector storage and high-performance cosine similarity queries.
    *   **SQLAlchemy**: Object-Relational Mapper (ORM) utilizing the async engine (`asyncpg` driver) for scalable, non-blocking transaction handles.
    *   **Alembic**: Lightweight database migration management environment tracking table upgrades and revision states.
*   **Caching & Coordination**:
    *   **Redis**: Key-value data cache running inside a container, preconfigured for future task queue structures.
*   **AI & Machine Learning Local Pipeline**:
    *   **ONNX Runtime**: Used locally (`onnxruntime.InferenceSession`) to execute embeddings execution bypasses on `Xenova/all-mpnet-base-v2`, dropping dynamic PyTorch/optimum library dependencies.
    *   **Tokenizers**: Fast Rust-backed tokenizer loaders (`tokenizers.Tokenizer`) to encode string representations before model execution.
*   **External Integration APIs**:
    *   **Ollama**: Host client interface to route prompt context arrays back to locally serving weights (`qwen2.5-coder:7b`).
    *   **HuggingFace Hub**: Downloader utility to fetch and locally cache model/tokenizer payloads.

---

## Detailed RAG Flow


The application follows a decoupled client-server architecture:

```mermaid
graph TD
    A[Streamlit UI] -->|HTTP Request| B[FastAPI Backend]
    B -->|API/Token| C[GitHub API]
    B -->|Store Chunks & Vectors| E[PostgreSQL + pgvector]
    B -->|RAG Context & Query| F[Local Ollama Server]
```

### 1. Ingestion & Pre-processing
*   **Git Diff Ingestion**: Uses remote Git blob SHA headers to determine if files have changed. Unmodified documents are skipped during update runs, avoiding redundant embedding computation.
*   **Document-Aware Chunking**: Files are split into code blocks using language-sensitive delimiters (e.g. classes, functions) while keeping logical headers attached to the payload context.
*   **ONNX Embedder**: Chunks are processed locally through `onnxruntime` utilizing the `Xenova/all-mpnet-base-v2` transformer model (768 dimensions), saving them directly to pgvector.

### 2. Search & Retrieval
*   **Dense Search**: Computes cosine distance similarity on pgvector columns mapping semantic intent.
*   **Sparse BM25 Search**: Matches exact keywords and code syntax structures across document properties.
*   **Hybrid Search (RRF)**: Combines dense and sparse results using Reciprocal Rank Fusion:
    $$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
    Where $r_m(d)$ is the rank of document $d$ in strategy $m$, and $k$ is a constant (default: `60`).
*   **Context Assembly**: Deduplicates retrieved code snippets and structures them into a clean XML-like schema matching LLM input tokens.

---

## Evaluation Pipeline

The evaluation suite (`backend/app/evaluation/evaluate_retrieval.py`) runs automated performance metrics comparing **Dense**, **BM25**, and **Hybrid** retrieval strategies across a ground-truth dataset.

### Key Metrics
1.  **Hit Rate (HR@K)**: Measures if the ground-truth document was retrieved in the top $K$ results.
2.  **Mean Reciprocal Rank (MRR@K)**: Evaluates the position of the first correct answer in the ranks:
    $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$

### Real Evaluation Results (RepoMind-AI ground-truth benchmark)
Below is the real evaluation table compiled by running 270 queries from our QA benchmark dataset directly against the ingested codebase on PostgreSQL + pgvector:

| Search Strategy | K | Hit Rate@K | MRR@K | Chunk Precision | Avg Latency (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BM25 (Sparse)** | 5 | 10.37% | 0.0287 | **100.00%** | **15.00** |
| **BM25 (Sparse)** | 10 | 21.48% | 0.0435 | **100.00%** | **15.00** |
| **pgvector (Dense)** | 5 | **40.00%** | **0.2151** | 82.22% | 15.20 |
| **pgvector (Dense)** | 10 | **55.93%** | **0.2350** | 91.67% | 15.20 |
| **Hybrid (RRF)** | 5 | 25.19% | 0.1137 | 90.37% | 758.73 |
| **Hybrid (RRF)** | 10 | 41.11% | 0.1354 | 96.67% | 602.54 |

> [!NOTE]
> Dense semantic search significantly outperforms BM25 keyword matching on codebase Q&A. This is because developer questions are written in natural English, whereas code snippets use programming language syntax, making exact keyword mapping (BM25) less effective. Furthermore, because BM25 query results are noisy for natural language queries, combining them with dense results via Reciprocal Rank Fusion (RRF) pulls down the top semantic matches, meaning dense search alone performs best.



---

## System Monitoring & Logs

### 1. Prometheus Metrics Dashboard
A dedicated instrumentation layer tracks API performance metrics:
*   `http_requests_total`: Counts incoming HTTP requests partitioned by endpoint, status code, and method.
*   `http_request_duration_seconds`: A histogram tracking response latencies across the ingestion and RAG engines.
*   `ollama_generation_duration_seconds`: Measures generation times for LLM completions.

### 2. Feedback Loop
User feedback is recorded directly via the `/api/v1/feedback` endpoint. Streamlit collects thumbs-up/down ratings and user comments, storing them in the Postgres `Feedback` table for post-evaluation query tuning.

---

## Development Best Practices

*   **Dependency Injection (DI)**: Follows clean FastAPI dependency patterns (`Depends`), injecting database sessions (`AsyncSession`) and configuration settings directly, easing unit-testing mock configurations.
*   **Structured Logging**: Utilizes `structlog` to output structured JSON logs, formatting traces, latencies, and transaction metrics for easy Elasticsearch/Grafana parsing.
*   **ONNX Local Optimizations**: Bypasses standard optimum library dependency conflicts by calling `onnxruntime.InferenceSession` and `tokenizers` directly. Model loading is warmed up once during FastAPI lifespan startup to eliminate runtime latency spikes.

---

## Known Issues & Workarounds

*   **Docker Container to Host Loopback**: Since the backend container needs to query the local Ollama instance on your host machine, direct `localhost` routing fails. The workaround is using Docker's bridge alias `http://host.docker.internal:11434` coupled with allowing external network calls inside Ollama settings (`OLLAMA_HOST=0.0.0.0`).
*   **Large File Tracking in Git History**: Downloading embedding weights directly inside the workspace folders results in extremely slow Git commit and push routines. To avoid this, model paths must be added to `.gitignore` and cached using local script modules (`download_model.py`) rather than repository builds.
*   **OneDrive Sync Collisions**: Running `uv sync` inside directory structures backed by OneDrive can throw OS errors (e.g. `os error 396`) due to incompatible cloud file hardlink handlers. Setting `--link-mode=copy` is required to bypass this.

---

## Future Improvements

*   **Asynchronous Ingestion Workers**: Integrate Celery or Arq backing tasks via Redis to support non-blocking repository ingestion of huge codebases without risking HTTP gateway timeouts.
*   **Graph RAG Integration**: Parse AST relationships and symbol reference structures to form codebase graphs, providing deeper contextual maps to the LLM during class/method queries.
*   **Cross-Encoder Reranking**: Deploy a local cross-encoder model (e.g., `bge-reranker-base`) to evaluate and sort initial candidate pools before assembling the prompt context.
*   **Multi-Repo Comparative Search**: Support querying across multiple ingested repositories simultaneously to help analyze dependency trees or shared internal libraries.
*   **Cloud Deployment Architecture**: Transition the stack to a scalable cloud architecture—deploying containerized services on AWS ECS/Fargate or GCP Cloud Run, utilizing AWS RDS (with pgvector) for database storage, and routing queries to managed LLM endpoints (like Bedrock or Gemini API) to replace local Ollama hardware requirements.


