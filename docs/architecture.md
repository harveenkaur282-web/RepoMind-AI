# System Architecture

This document details the system design, layering, and responsibilities of each module in the **RepoMind-AI** workspace.

---

## System Flow & Component Responsibilities

The system is structured as a decoupled web application with four primary layers:

```
[ Streamlit Client UI ] 
        │  (HTTP / JSON)
        ▼
[ FastAPI Server Routing ] ◄───► [ SQLAlchemy Async DB ORM ] ◄───► [ PostgreSQL / pgvector ]
        │  (Service Orchestration)
        ▼
[ RAG Pipeline Orchestrator ]
        ├──► [ Query Rewriter ] ────► (Vague to code-optimized queries)
        ├──► [ Retrieval Service ] ──► (Dense / BM25 / Hybrid)
        ├──► [ Document Reranker ] ──► (Local Cross-Encoder ranking)
        ├──► [ Context Assembler ] ──► (Deduplication, Token Capping)
        └──► [ LLM Provider ] ───────► (Ollama / OpenRouter / Gemini / Groq)
```

---

## 1. Frontend Client (Streamlit)
*   **Location**: `frontend/streamlit/`
*   **Responsibilities**:
    *   **User Interface**: Renders pages for Repository Ingestion, Repository Dashboard lists, AI Assistant Chat interface, and the Developer Console.
    *   **State Management**: Manages user chat histories locally in `st.session_state` (resetting them when switching repositories).
    *   **API Client**: Uses `utils/api.py` to communicate with the FastAPI backend via `httpx`.

---

## 2. API Routing Layer (FastAPI)
*   **Location**: `backend/app/api/v1/endpoints/`
*   **Responsibilities**:
    *   `health.py`: Diagnostics checking database analytics counts and status.
    *   `ingestion.py`: Repository initial ingestion and incremental update tasks.
    *   `repositories.py`: Listing and deleting repository entities (triggering cascade deletions of associated documents/chunks in the database).
    *   `rag.py`: Endpoint for executing RAG queries and side-by-side strategy comparisons.

---

## 3. Storage Layer (PostgreSQL & SQLAlchemy)
*   **Location**: `backend/app/db/`
*   **Responsibilities**:
    *   **ORM Models**: Defines `Repository`, `Document`, and `Chunk` tables.
    *   **pgvector integration**: Stores chunk vector embeddings in `voyage_embedding` columns utilizing the pgvector extension for Cosine Similarity searches.
    *   **Cascade deletion**: Declares `cascade="all, delete-orphan"` relations so that dropping a repository safely wipes its children documents and chunks from the database automatically.

---

## 4. RAG Services Layer
*   **Location**: `backend/app/services/`
*   **Responsibilities**:
    *   **Query Rewriter**: `QueryRewriter` parses conversational queries and rewrites them into code-specific search tokens.
    *   **Retrieval**: `RetrievalService` resolves queries against the database using BM25, dense vector, or hybrid rank fusion scoring.
    *   **Reranking**: `LocalCrossEncoderReranker` scores candidate results using token intersection and path-component matching to surface the most relevant chunks.
    *   **Context Assembly**: `ContextAssembler` filters, deduplicates by ID, maps file paths, and truncates matching chunks to fit inside token boundaries.
    *   **LLM Provider**: `OllamaProvider`, `GeminiProvider`, `GroqProvider`, and `OpenRouterProvider` connect to local/hosted LLM servers, normalizing exceptions into custom `LLMProviderError` boundaries.
    *   **RAG Service**: `RAGService` acts as the coordinator, sequentially invoking rewriting, retrieval, reranking, context assembly, and LLM providers.

---

## 5. Evaluation Layer
*   **Location**: `backend/app/evaluation/`
*   **Responsibilities**:
    *   **Pydantic Models**: Defines evaluation datasets and question/ground-truth validation schema.
    *   **Dataset Storage**: Located in `evaluation/data/` as versioned JSON datasets containing manually verified codebase queries.
