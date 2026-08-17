# Setup and Environment Variables

Follow these instructions to configure and run **RepoMind-AI** locally.

---

## Required Environment Variables

Create a `.env` file in the root directory (based on `.env.example`). The following variables are configured:

| Variable | Description | Default Value | Required? |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | The title of the application | `"RepoMind AI"` | No |
| `DATABASE_URL` | The PostgreSQL database connection URL | `"postgresql://postgres:postgres@localhost:5432/repomind"` | Yes |
| `REDIS_URL` | Redis connection URL | `"redis://localhost:6379"` | No |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `""` | Strongly Recommended |
| `LLM_PROVIDER` | The active text generation provider | `"ollama"` | Yes |
| `VOYAGE_API_KEY` | Voyage AI API key for embedding generation | `""` | Yes |
| `OLLAMA_URL` | Local Ollama server endpoint | `"http://localhost:11434"` | Yes (if using Ollama) |
| `OLLAMA_MODEL` | Local Ollama chat model to query | `"qwen2.5-coder:7b"` | Yes (if using Ollama) |

---

## Detailed Local Setup

### 1. Database (PostgreSQL + pgvector & Redis)
The database is run via Docker. Ensure Docker Desktop is active.
```bash
docker-compose up -d
```
*   **Postgres Container**: named `repomind-postgres` on port `5432`.
*   **Redis Container**: named `repomind-redis` on port `6379`.

### 2. Alembic migrations
Once the database container is started, initialize the database tables by running migrations:
```bash
uv run alembic upgrade head
```
*(The migration script automatically runs `CREATE EXTENSION IF NOT EXISTS vector` to initialize pgvector before creating table schemas).*

### 3. Local LLM (Ollama)
Download and run the Ollama client locally. Pull the default code model:
```bash
ollama pull qwen2.5-coder:7b
```

### 4. Running Backend Server
```bash
uv run uvicorn backend.app.main:app --port 8000 --reload
```
*   Exposes endpoints on `http://localhost:8000`.
*   Interactive API Swagger docs are available at `http://localhost:8000/docs`.

### 5. Running Streamlit App
```bash
uv run streamlit run frontend/streamlit/app.py --server.port 8501
```
*   Opens the frontend client in your web browser at `http://localhost:8501`.
