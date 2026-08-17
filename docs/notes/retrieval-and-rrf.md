# Learning Notes: Retrieval & Reciprocal Rank Fusion (RRF)

These notes cover our math formulations and observations regarding Dense, Sparse (BM25), and Hybrid retrieval.

---

## 1. BM25 (Sparse) Implementation
*   Our self-contained BM25 algorithm tokenizes text using regular expressions to filter code syntax symbols.
*   IDF is calculated dynamically over all chunks in the target repository.
*   Document length normalization is handled using document average lengths.
*   *Edge case*: If the repository is completely empty, average document length is `0`. We protected against this by adding checks to prevent `ZeroDivisionError`.

---

## 2. Dense (Vector) Retrieval
*   Utilizes Voyage's `voyage-code-3` model (optimized for code repositories) producing 1024-dimension float vectors.
*   Uses PostgreSQL's `pgvector` index structure to execute Cosine Similarity operations:
    $$\text{Cosine Distance} = 1 - \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$
    which maps to the `<=>` operator.

---

## 3. Reciprocal Rank Fusion (RRF)
RRF is a simple but highly effective algorithm to combine search strategies without needing to normalize scores into the same range (since BM25 returns unbounded floats, while Cosine Similarity returns values between 0 and 1).

*   **RRF scoring formula**:
    $$\text{RRF\_Score}(c) = \frac{1}{k + r_{\text{dense}}(c)} + \frac{1}{k + r_{\text{bm25}}(c)}$$
    where we set $k = 60$ (the standard constant weight parameter in RRF research).
*   **Result**: Chunks that rank highly in both dense and sparse strategies get boosted to the very top, while items that only match one strategy still maintain a sensible retrieval ranking.
