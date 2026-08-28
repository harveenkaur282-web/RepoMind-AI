# Future Work & Architectural Roadmap

This document outlines the planned future enhancements and architectural upgrades for RepoMind-AI to push retrieval performance (Hit Rate and MRR) and extend codebase intelligence capabilities.

---

## 1. Abstract Syntax Tree (AST) Semantic Chunking (Tree-Sitter)

* **Current Implementation**: Code documents are split using fixed-character and line-based boundaries with basic language delimiters. This can split functions, classes, or decorators mid-definition.
* **Proposed Enhancement**:
  * Integrate **Tree-Sitter** to parse Abstract Syntax Trees across Python, TypeScript, JavaScript, Go, and Rust.
  * Construct chunks strictly along semantic code boundaries (`FunctionDef`, `ClassDef`, `MethodDef`).
  * **Header Signature Injection**: Prepend full file paths, class names, function signatures, and docstrings to every chunk:
    ```python
    # File: backend/app/services/retrieval/service.py
    # Class: RetrievalService | Method: search()
    ```

---

## 2. Hierarchical Parent-Child & File Summary Indexing

* **Current Implementation**: Flat chunk indexing into PostgreSQL `pgvector`. A single large file produces ~10 chunks, causing multi-chunk retrieval competition that dilutes Top-K relevance and lowers Mean Reciprocal Rank (MRR).
* **Proposed Enhancement**:
  * **Two-Tier Retrieval Architecture**: Generate 2-line file summaries and docstring vectors for a **Parent File Index**.
  * **File-First Matching**: First retrieve the target parent file at Rank #1 (boosting MRR from 0.26 to 0.65+), then pull relevant child chunks within that matched file.

---

## 3. Code-Specialized Vector Embedding Models

* **Current Implementation**: `Xenova/bge-base-en-v1.5` (768-dimensional local ONNX model).
* **Proposed Enhancement**:
  * Upgrade to code-native embedding models pretrained on AST tokens, identifier syntax, and code-comment pairs:
    * `jina-embeddings-v2-base-code` (8192-token context window)
    * `nomic-embed-text-v1.5`
    * `voyage-code-2` / `text-embedding-3-small`

---

## 4. HyDE (Hypothetical Document Embeddings) & Query Expansion

* **Current Implementation**: Direct vector embedding of user natural language queries.
* **Proposed Enhancement**:
  * **HyDE Pipeline**: Use a lightweight local LLM pass to translate natural language user questions (e.g., *"Where is JWT authentication validated?"*) into hypothetical code signatures (e.g., `def verify_jwt_token(token: str)...`).
  * Embed the generated hypothetical code snippet to query pgvector, dramatically increasing cosine similarity with ground-truth code definitions.

---

## 5. Symbol & Import Knowledge Graphs

* **Current Implementation**: Chunks are evaluated in isolation without caller/callee context.
* **Proposed Enhancement**:
  * Build a repository-wide dependency graph tracking function calls, imports, and interface implementations.
  * Inject caller/callee metadata into chunk embeddings for graph-guided context expansion during answer generation.

---

## 6. GitHub Issues & Pull Request Integration

* **Current Implementation**: Codebase file and chunk indexing.
* **Proposed Enhancement**:
  * Index GitHub Issues, Pull Requests, Commit messages, and Code Review discussions alongside the codebase.
  * Serve as a comprehensive developer onboarding assistant capable of answering questions about past bugs, architectural decisions, and PR history.
