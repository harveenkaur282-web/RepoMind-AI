# Retrieval Strategies

RepoMind-AI implements multiple retrieval strategies, query optimization, and post-retrieval re-scoring to search codebase repositories.

---

## 1. Dense (Vector) Retrieval
*   **How it works**:
    *   Generates 1024-dimension embeddings for code chunks using the `voyage-code-3` model.
    *   Generates a query embedding vector at search time using `VoyageEmbeddingProvider.embed_query`.
    *   Queries PostgreSQL using the cosine distance operator (`<=>` in `pgvector`) to find semantic similarity.
*   **Best for**: Understanding conceptual questions, synonym mapping (e.g., matching "database session" to "engine configuration"), and natural language explanations.

---

## 2. Sparse (BM25) Retrieval
*   **How it works**:
    *   Uses a self-contained python BM25 implementation.
    *   Tokenizes database chunks using an alphanumeric regular expression tokenizer and calculates Inverse Document Frequency (IDF) statistics across the ingested document corpus:
        $$\text{IDF}(q) = \ln\left(\frac{N - n(q) + 0.5}{n(q) + 0.5} + 1\right)$$
    *   Scores code chunks based on term matching frequency and document length normalization (averaging document sizes to scale long files down).
*   **Best for**: Matching exact code symbols, variable names, class names, specific decorators (e.g. `@router.post`), and unique filenames.

---

## 3. Hybrid (RRF) Retrieval
*   **How it works**:
    *   Executes both the **Dense** and **BM25** queries in parallel.
    *   Fuses the results using the **Reciprocal Rank Fusion (RRF)** algorithm:
        $$\text{RRF\_Score}(c) = \frac{1}{60 + r_{\text{dense}}(c)} + \frac{1}{60 + r_{\text{bm25}}(c)}$$
        where $r_{\text{dense}}(c)$ and $r_{\text{bm25}}(c)$ are the integer ranks of the chunk in each search strategy.
    *   Sorts chunks in descending order of their fused RRF score and returns the top $K$ items.
*   **Best for**: General queries that require both semantic understanding (why things happen) and exact term matching (where specific functions are defined).

---

## 4. Query Rewriting Layer
*   **How it works**:
    *   Uses the configured LLM provider to clean up and structure natural language queries.
    *   Strips conversational headers (e.g. "hey, can you find...") and returns clean, search-friendly tokens.
*   **Benefit**: Greatly improves BM25 matching and semantic hits for vague user queries.

---

## 5. Document Reranking (Cross-Encoder)
*   **How it works**:
    *   A post-retrieval scoring step using `LocalCrossEncoderReranker`.
    *   Tokenizes candidates at the identifier level (breaking CamelCase and snake_case) and calculates overlaps, phrase sequences, and path-component matches.
*   **Benefit**: Scores document chunks directly against the search query, reordering candidate lists to float the most contextually relevant code blocks to the top.

---

## Evaluation Dataset
We have created a versioned evaluation dataset in `evaluation/data/retrieval_dataset_v1.json` with ground-truth codebase queries. We will use this dataset to evaluate and compare:
1.  Dense Retrieval
2.  BM25 Retrieval
3.  Hybrid (RRF) Retrieval
4.  Hybrid + Query Rewriting
5.  Hybrid + Reranking

We will measure performance using metrics like **Hit Rate** and **MRR** (Mean Reciprocal Rank).
