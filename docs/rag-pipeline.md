# RAG Pipeline Flow

This document details the step-by-step pipeline executed when a query is handled by **RepoMind-AI**.

---

## RAG Pipeline Stages

```
[ User Query ]
     │
     ▼
[ Step 1: Query Rewriting (Optional) ] ──► Optimize search keywords using LLM
     │
     ▼
[ Step 2: Retrieval ] ──────────────────► Query Database (Dense / BM25 / Hybrid)
     │
     ▼
[ Step 3: Document Reranking (Optional) ] ► Local Cross-Encoder ranking
     │
     ▼
[ Step 4: Context Assembly ] ───────────► Deduplicate, format, and enforce Token Capping
     │
     ▼
[ Step 5: LLM Generation ] ─────────────► Build System Prompt, post to LLM Provider
     │
     ▼
[ Step 6: Final Output ] ───────────────► Return structured Answer & Source Chunks to UI
```

---

## Step 1: Query Rewriting (Optional)
*   If enabled, the `QueryRewriter` uses the active LLM provider to rewrite vague or conversational queries into code-search-optimized phrases.
*   Conversational filler is stripped; file names, code syntax symbols, and exact technologies are preserved.

---

## Step 2: Retrieval
*   The orchestrator (`RAGService`) receives the query (rewritten if enabled) and runs the retrieval strategy (`dense`, `bm25`, or `hybrid`).
*   If reranking is enabled, a larger initial pool (e.g. 20 or 50 chunks) is retrieved.
*   If vector matching is active, the query (or rewritten search query) is embedded.

---

## Step 3: Document Reranking (Optional)
*   If enabled, the `LocalCrossEncoderReranker` scores candidates using a lightweight cross-encoder simulator.
*   Matches terms at the token and sub-token level (splitting CamelCase and snake_case) and rewards path-component overlaps.
*   Reorders candidates descending by rerank score, then slices back to the target final size (default top 10).

---

## Step 4: Context Assembly
*   `ContextAssembler` processes the retrieved chunks:
    1.  **Deduplication**: Removes duplicate chunks by `chunk.id` while preserving relative rank.
    2.  **Formatting**: Wraps each chunk inside clear Markdown blocks denoting file path.
    3.  **Token Capping**: Enforces token budgets (e.g. `max_tokens=4000`), truncating gracefully to fit the context window.

---

## Step 5: LLM Generation
*   Supports three distinct prompt strategies:
    *   `concise_grounded`: Short answers, strictly grounded in context.
    *   `detailed_grounded`: Detailed code explanation, explicitly flagging insufficient context.
    *   `developer_assistant`: Senior developer persona, highlighting paths, and distinguishing evidence from inference.
*   Sends the assembled context and system prompt to the configured LLM provider (`ollama`, `openrouter`, `gemini`, or `groq`), validating credentials beforehand.

---

## Step 6: Final Output
*   Compiles results into a `RAGResponse` containing:
    *   The generated answer text.
    *   The matching chunks, complete with original and reranked scores.
    *   Metadata (prompt strategy, strategy used, token counts, etc.).
