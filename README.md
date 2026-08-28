# RepoMind-AI

A workspace for indexing, searching, and discussing GitHub codebases using RAG (Retrieval-Augmented Generation). It runs entirely locally inside Docker containers. In the future, this will extend to indexing issues and pull requests, serving as an onboarding tool for developers joining new projects.

![RepoMind-AI Assistant Interface](screenshots/Screenshot%202026-08-21%20092156.png)

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

```text
========================================================================================================================
                                             REPOMIND-AI SYSTEM ARCHITECTURE
========================================================================================================================

 [ CLIENT PRESENTATION LAYER ]
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                           Streamlit Workspace UI                                                 │
  │     (Repository Ingestion  *  Interactive RAG Chat  *  Side-by-Side Strategy Playground  *  Dev Console)         │
  └────────────────────────────────────────┬─────────────────────────────────────────────────────────┘
                                           │ HTTP REST / JSON API Calls
                                           ▼
 [ API & ORCHESTRATION LAYER ]
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                        Async API Server (FastAPI)                                                │
  │  ┌───────────────────────┐   ┌────────────────────────┐   ┌──────────────────────────┐   ┌────────────────────┐  │
  │  │  Ingestion Router     │   │  RAG Query Router      │   │  Repository Router       │   │ Monitoring Service │  │
  │  │  POST /ingestion/repo │   │  POST /rag/query       │   │  GET/DELETE /repos       │   │ Structlog Tracker  │  │
  │  └───────────┬───────────┘   └───────────┬────────────┘   └──────────────────────────┘   └─────────┬──────────┘  │
  └──────────────┼───────────────────────────┼─────────────────────────────────────────────────────────┼─────────────┘
                 │                           │                                                         │
       (1. Async Ingestion)         (2. Hybrid RAG Query)                                     (3. Metrics & Logs)
                 │                           │                                                         │
                 ▼                           ▼                                                         ▼
 [ INGESTION PIPELINE ]          [ SEARCH & RETRIEVAL ENGINE ]                                [ OBSERVABILITY LAYER ]
  ┌──────────────────────────┐    ┌──────────────────────────────────────────────────────┐    ┌──────────────────────┐
  │ GitHub REST API Crawler  │    │  ┌───────────────────┐    ┌───────────────────────┐  │    │ PostgreSQL Database  │
  │ (Git Blob SHA Check)     │    │  │ Query Rewriter    │    │ Context Assembler     │  │    │ RAG Events & Feedback│
  └──────────────┬───────────┘    │  │ (LLM Expansion)   │    │ (XML Context Wrapper) │  │    └──────────┬───────────┘
                 │                │  └─────────┬─────────┘    └───────────▲───────────┘  │               │
                 ▼                │            │                          │              │               ▼
  ┌──────────────────────────┐    │            ▼                          │              │    ┌──────────────────────┐
  │ Language-Aware Chunker   │    │  ┌───────────────────┐                │              │    │ Grafana Dashboards   │
  │ (AST / Structural Splits)│    │  │ Dense Search      ├────────┐       │ (Top Reranked│    │ Latencies, Tokens &  │
  └──────────────┬───────────┘    │  │ (pgvector Cosine) │        │       │   Context)   │    │ Feedback Analytics)  │
                 │                │  └───────────────────┘        ▼       │              │    └──────────────────────┘
                 ▼                │                         ┌─────────────┴──────────┐   │
 [ LOCAL ONNX INFERENCE ]         │  ┌───────────────────┐  │  Hybrid Rank Merger    │   │
  ┌──────────────────────────┐    │  │ Sparse Search     ├──┤  (Reciprocal Rank      │   │
  │ Local Vector Embedder    │    │  │ (In-Memory BM25)  │  │   Fusion RRF)          │   │
  │ (bge-base-en-v1.5)       │    │  └───────────────────┘  └─────────────┬──────────┘   │
  │ 768-dim Vector Weights   │    │                                       │              │
  └──────────────┬───────────┘    │                                       ▼              │
                 │                │                         ┌────────────────────────┐   │
                 ▼                │                         │ ONNX Cross-Encoder     │   │
 [ PERSISTENCE & STORAGE ]        │                         │ Neural Reranker        │   │
  ┌──────────────────────────┐    │                         │ (bge-reranker-base)    │   │
  │ PostgreSQL + pgvector    │    │                         └────────────────────────┘   │
  │ (hnsw / ivfflat indexes) │    └──────────────────────────────────────────────────────┘
  └──────────────────────────┘                                            │
                                                                          │ Prompt + Context
                                                                          ▼
                                                          [ GENERATION PROVIDER ROUTER ]
                                                           ┌─────────────────────────────────────────────────────────┐
                                                           │ * Local Ollama (qwen2.5-coder:7b)                       │
                                                           │ * Cloud Fallback (Groq / Gemini / OpenRouter)           │
                                                           └─────────────────────────────────────────────────────────┘
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

Evaluated across a 270-query ground-truth benchmark dataset:

| Retrieval Strategy | Reranker | Hit Rate@10 | MRR@10 | Chunk Precision | Avg Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Dense + Rerank** | Yes | **69.26%** | **0.2657** | 96.11% | 9.5s |
| **Hybrid + Rerank** | Yes | 60.00% | 0.2393 | 97.41% | 11.1s |
| **Dense (Vector Search)** | No | 59.63% | 0.2287 | 97.96% | **145ms** |
| **BM25 (Sparse)** | No | 24.81% | 0.0503 | 100.00% | 701ms |

* **Neural Reranking Gain**: Neural cross-encoder reranking boosts Hit Rate@10 to **69.26%**.
* **Ultra-Fast Vector Option**: Un-reranked dense search delivers **145ms** latency with a 59.63% hit rate.

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

## Future Work

* **LLM-as-a-Judge Evaluation**: Measure answer quality and accuracy automatically using LLMs to score answer relevance and faithfulness.
* **Pull Requests, Issues & Discussions**: Expand indexing beyond code files to include GitHub PRs, Issues, and Discussions to improve retrieval quality (MRR).
* **Repository Ingestion Speed**: Optimize file parsing and track the time duration required to index large codebases.
* **Multi-Repository Search**: Enable indexing and asking questions across multiple repositories at the same time in a single workspace.



