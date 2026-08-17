# RAG Pipeline Flow

This document details the step-by-step pipeline executed when a query is handled by **RepoMind-AI**.

---

## The Four Stages of the Pipeline

```
[ User Query ]
     │
     ▼
[ Step 1: Retrieval ] ──────────► Query Database (Dense / BM25 / Hybrid)
     │
     ▼
[ Step 2: Context Assembly ] ───► Deduplicate, format layout, and enforce Token Capping
     │
     ▼
[ Step 3: LLM Generation ] ─────► Build System Prompt, post to local Ollama /api/chat
     │
     ▼
[ Step 4: Final Output ] ───────► Return structured Answer & Source Chunks to client UI
```

---

## Step 1: Retrieval
*   The orchestrator (`RAGService`) receives the user query, strategy (`dense`/`bm25`/`hybrid`), and repository ID.
*   If vector-based matching (`dense` or `hybrid`) is selected, the query is embedded using `VoyageEmbeddingProvider.embed_query`.
*   `RetrievalService.search` queries the database to return the top candidate code chunks.
*   FastAPI ensures SQLAlchemy relationship eager loading (`selectinload(Chunk.document)`) is used so file paths are pre-fetched.

---

## Step 2: Context Assembly
*   `ContextAssembler` processes the retrieved chunks:
    1.  **Deduplication**: Removes duplicate chunks by `chunk.id` while preserving relative rank.
    2.  **Formatting**: Wraps each chunk inside clear Markdown blocks denoting file path and strategy context:
        ```markdown
        ---
        File: backend/app/main.py
        ---
        [Code chunk content here]
        ```
    3.  **Token Capping**: Uses a character-count multiplier estimation (or custom token callable) to fill up to the configured token budget (e.g. `max_tokens=4000`), truncating gracefully without cutting off in the middle of code files if possible.

---

## Step 3: LLM Generation
*   The system prompt instructs the assistant on how to behave:
    *   Explain code clearly like a professional senior developer.
    *   State honestly if the answer cannot be found in the provided context rather than inventing solutions.
*   Translates parameters and context into the Ollama JSON payload.
*   Issues an async HTTP request to local Ollama chat endpoints (`/api/chat`).
*   Catches HTTP timeouts, connection failures, or malformed JSON formats, wrapping them inside a domain-level `LLMProviderError` exception.

---

## Step 4: Final Output
*   Compiles results into a `RAGResponse` object containing:
    *   The generated answer text.
    *   The list of matching source chunks (used in Streamlit to render the source explorer cards).
    *   Metadata (total chunks retrieved, token consumption count, active strategy).
