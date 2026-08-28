# RepoMind-AI

A workspace for indexing, searching, and discussing GitHub codebases using RAG (Retrieval-Augmented Generation). It runs entirely locally inside Docker containers. In the future, this will extend to indexing issues and pull requests, serving as an onboarding tool for developers joining new projects.

![RepoMind-AI Assistant Interface](screenshots/Screenshot%202026-08-23%20043319.png)

---

## How to Run the Project

You can run RepoMind-AI fully containerized. It uses a local ONNX embedding model (`Xenova/bge-base-en-v1.5`, 768 dimensions) and a local ONNX Neural Cross-Encoder Reranker (`Xenova/bge-reranker-base`) to avoid external API costs and connects to Ollama on your host machine.

### Prerequisites
* **Docker Desktop** (must be running on your machine)
* **Ollama** (installed and running on your host machine)
* **Python 3.12+** (optional, for local tests)

### Setup Instructions

1. **Clone the repo**
   ```bash
   git clone https://github.com/harveenkaur282-web/RepoMind-AI.git
   cd RepoMind-AI
   ```

2. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   APP_NAME=RepoMind AI
   ENVIRONMENT=development
   DEBUG=true

   # PostgreSQL and Redis setup
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/repomind
   REDIS_URL=redis://redis:6379/0

   # LLM Choice (Groq, Gemini, or Ollama)
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=openai/gpt-oss-20b

   # Needed for private repositories or rate limits
   GITHUB_TOKEN=your_github_token_here
   ```

3. **Download the local embedding and reranker models**
   Run this to download the ONNX model weights before starting Docker:
   ```bash
   uv run python backend/app/download_model.py
   ```

4. **Spin up the containers**
   Build and start Postgres, Redis, Grafana, Streamlit, and FastAPI:
   ```bash
   docker compose up --build -d
   ```

5. **Run database migrations**
   ```bash
   docker compose exec backend uv run alembic upgrade head
   ```

6. **Pull the LLM model in Ollama**
   Ensure Ollama is running on your machine, then pull the coder model:
   ```bash
   ollama pull qwen2.5-coder:7b
   ```

7. **Open the applications**
   * **Streamlit UI**: `http://localhost:8501`
   * **FastAPI Docs**: `http://localhost:8000/docs`
   * **Grafana Dashboard**: `http://localhost:3000` (Login: `admin` / `admin`)

---

## File Structure

```
├── alembic/                      # Database migrations
├── backend/
│   ├── Dockerfile                # FastAPI backend container
│   └── app/
│       ├── api/                  # API routers and endpoints (RAG, Repositories, Feedback)
│       ├── core/                 # App configurations and db setup
│       ├── db/                   # SQLAlchemy models (Chunks, Documents, Feedback, RAGEvents)
│       ├── evaluation/           # RAG retrieval benchmark execution scripts
│       ├── monitoring/           # Structlog config and event tracking service
│       └── services/
│           ├── chunking/         # Custom parsers (Recursive and Language-Aware chunking)
│           ├── embeddings/       # Embedding providers (Local ONNX bge-base-en-v1.5)
│           ├── generation/       # LLM clients (Ollama, Groq, OpenRouter, Gemini)
│           ├── rag/              # Neural ONNX Cross-Encoder Reranker (bge-reranker-base)
│           └── retrieval/        # Dense (pgvector) and Sparse (BM25) search implementations
├── docs/                         # Architecture, PRD, and implementation notes
├── evaluation/                   # Offline evaluation datasets (v1, v2) and benchmark results
├── frontend/
│   ├── Dockerfile                # Streamlit frontend container
│   └── streamlit/
│       └── app.py                # Streamlit entrypoint & multi-page navigation
├── grafana/                      # Dynamic provisioning script and dashboard templates
├── FUTURE_WORK.md                # Architectural roadmap and future improvements
├── screenshots/                  # UI and Grafana screenshots
├── docker-compose.yml            # Multi-service setup
└── pyproject.toml                # Project configurations and dependencies
```


---

## Core Technologies

* **FastAPI**: Runs the asynchronous API backend. It pre-loads the embedding model on startup.
* **Streamlit**: Renders the frontend chat UI and repository management pages.
* **PostgreSQL & pgvector**: Stores ingested chunks and runs vector similarity queries.
* **SQLAlchemy & Alembic**: Manages database access via async drivers (`asyncpg`) and schema migrations.
* **ONNX Runtime**: Runs the `Xenova/bge-base-en-v1.5` 768-dim vector embedding model and `Xenova/bge-reranker-base` Neural Cross-Encoder locally.
* **Ollama**: Connects the workspace to local open-weight models like `qwen2.5-coder:7b`.
* **Redis**: Preconfigured in the container stack (prepared for future rate-limiting and query caching).

---

## System Architecture

```mermaid
graph TB
    subgraph Client ["Frontend Layer"]
        UI["Streamlit Workspace UI"]
    end

    subgraph API ["Async API Server (FastAPI)"]
        Ingest["Repository Ingestion Engine"]
        Chunker["Language-Aware Chunker"]
        RAGRouter["RAG Query Orchestrator"]
        LLMRouter["Multi-LLM Provider Router"]
        Monitor["Monitoring & Metrics Service"]
    end

    subgraph Models ["Local Machine Learning Inference (ONNX)"]
        Embedder["Local Vector Embedder<br/>(bge-base-en-v1.5)"]
        Reranker["Neural Cross-Encoder Reranker<br/>(bge-reranker-base)"]
    end

    subgraph Storage ["Persistence & Retrieval Layer"]
        PG[("PostgreSQL + pgvector<br/>(Vector Similarity Search)")]
        BM25["In-Memory BM25 Index<br/>(Sparse Keyword Match)"]
        RRF["Reciprocal Rank Fusion<br/>(Hybrid Rank Merger)"]
        Redis[("Redis Cache")]
    end

    subgraph LLMs ["LLM Generation Providers"]
        Ollama["Local Ollama<br/>(qwen2.5-coder:7b)"]
        CloudLLM["Cloud LLMs<br/>(Groq / Gemini / OpenRouter)"]
    end

    subgraph Observability ["Observability Layer"]
        Grafana["Grafana Dashboards<br/>(Latencies, Tokens & Feedback)"]
    end

    UI -->|HTTP Requests| API
    Ingest -->|Raw Code Files| Chunker
    Chunker -->|Text Chunks| Embedder
    Embedder -->|768-dim Vectors| PG
    
    RAGRouter -->|Query Text| Embedder
    RAGRouter -->|Dense Search| PG
    RAGRouter -->|Sparse Search| BM25
    PG & BM25 -->|Candidate Hits| RRF
    RRF -->|Top Candidate Pool| Reranker
    Reranker -->|Cross-Encoder Scores| RAGRouter
    
    RAGRouter -->|Context & System Prompt| LLMRouter
    LLMRouter -->|Local Pipeline| Ollama
    LLMRouter -->|Cloud Fallback| CloudLLM
    
    API -->|RAG Events & Metrics| Monitor
    Monitor -->|Analytics Data| Grafana
```


1. **Ingestion**: The system checks file modifications via Git blob SHAs to avoid re-embedding unchanged documents.
2. **Chunking**: Code documents are split by functions and classes using language delimiters (Python, JavaScript, etc.).
3. **Retrieval**: 
   * **Dense**: Cosine similarity search over pgvector columns using `Xenova/bge-base-en-v1.5`.
   * **Sparse**: Key-phrase match using local BM25 indexing.
   * **Hybrid**: Merges sparse and dense results using Reciprocal Rank Fusion (RRF).
4. **Reranking**: Uses `Xenova/bge-reranker-base` ONNX cross-encoder to re-score candidate chunks.
5. **Answer Generation**: Deduplicates the best chunks, packages them into an XML context wrapper, and queries the LLM.

---

## Evaluation Benchmark

We evaluated our retrieval strategies using a 270-query ground-truth dataset against the codebase:

| Search Strategy | K | Reranker | Hit Rate@K | MRR@K | Chunk Precision | Avg Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **dense+rerank** | **10** | **Yes** | **69.26%** | **0.2657** | **96.11%** | 9509.57 |
| **hybrid+rerank** | **10** | **Yes** | **60.00%** | **0.2393** | **97.41%** | 11126.58 |
| **dense** | **10** | No | **59.63%** | **0.2287** | **97.96%** | **145.46** |
| **dense+rerank** | **5** | **Yes** | **50.37%** | **0.2403** | 86.11% | 11607.41 |
| **hybrid+rerank** | **5** | **Yes** | **46.30%** | **0.2206** | 87.22% | 12442.92 |
| **hybrid** | **10** | No | **44.81%** | 0.1199 | **100.00%** | 844.39 |
| **dense** | **5** | No | **41.85%** | 0.2055 | 93.70% | **162.73** |
| **hybrid** | **5** | No | **25.56%** | 0.0941 | 97.78% | 878.26 |
| **bm25** | **10** | No | **24.81%** | 0.0503 | **100.00%** | 701.67 |
| **bm25** | **5** | No | **11.85%** | 0.0328 | **100.00%** | 792.56 |


### Evaluation Insights
* **Neural Reranking Gain**: Adding `Xenova/bge-reranker-base` cross-encoder reranking boosts Hit Rate@10 from **59.63% to 69.26%** (+9.63% absolute gain) 
* **Dense vs. Sparse**: Dense vector search (`Xenova/bge-base-en-v1.5`) significantly outperforms BM25 keyword matching as well as hybrid approach (done using rrf) 
* **Low Latency Option**: Un-reranked `dense` search at $K=10$ provides a fast 145ms response time while maintaining a 59.63% hit rate.


---

## Monitoring with Grafana

This project includes a pre-configured Grafana monitoring dashboard tracking database size, endpoint latencies, errors, and user feedback ratings.

### Setting Up Monitoring
Run the dynamic provisioning script from your host machine to set up the datasource and dashboard:
```bash
# Set your custom admin password (if changed from the default 'admin')
export GRAFANA_ADMIN_PASSWORD="your_password"

# Run setup
uv run python grafana/init.py
```
Visit the dashboard at `http://localhost:3000/d/bfvzqom4t1on4a/repomind-ai-monitoring`.

---

## Limitations

* **Container Loopback**: Referencing host-bound Ollama services from the Docker backend container requires mapping loopback URLs (`http://host.docker.internal:11434`) and allowing open network configurations in your Ollama host setup (`OLLAMA_HOST=0.0.0.0`).
* **Local Model Caching**: ONNX embedding models are omitted from repository builds to prevent git slowdowns, requiring local downloading scripts before running container setups.
* **Windows OneDrive Collisions**: Windows environments syncing through OneDrive collide with virtual environment hardlinks during compilation, requiring `uv sync --link-mode=copy` modifications.
* **In-Memory BM25**: BM25 scores are evaluated in-memory over database-fetched document lists, making indexing scale linearly with CPU capacity for massive repositories.

