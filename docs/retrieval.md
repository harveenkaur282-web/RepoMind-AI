# Retrieval Strategies

RepoMind-AI implements three different retrieval strategies to search codebase repositories.

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

## Why We Implemented All Three
We implemented all three strategies to allow for **Retrieval Evaluation**:
*   Dense search is powerful for broad conceptual sweeps but can easily lose track of exact matching variable names or function symbols.
*   BM25 is highly precise for keyword matching but fails if the user asks a question using synonyms.
*   Hybrid search aims to bridge the gap.
*   *Planned Evaluation*: During the evaluation phase, we will grade each strategy using metrics like **Hit Rate** and **MRR** (Mean Reciprocal Rank) to mathematically determine which strategy performs best for codebase search.
