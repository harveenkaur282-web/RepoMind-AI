from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.models.chunk import Chunk
from backend.app.db.models.document import Document


def tokenize(text: str | None) -> list[str]:
    """Tokenize text into lowercase alphanumeric words."""
    if not text:
        return []
    return re.findall(r"\w+", text.lower())


class BM25:
    """Lightweight BM25 ranking implementation."""

    def __init__(
        self,
        corpus: list[list[str]],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = (
            sum(len(doc) for doc in corpus) / self.corpus_size if self.corpus_size > 0 else 0
        )
        self.doc_freqs: list[dict[str, int]] = []
        self.idf: dict[str, float] = {}
        self.doc_len: list[int] = []
        self._initialize(corpus)

    def _initialize(self, corpus: list[list[str]]) -> None:
        nd: dict[str, int] = {}
        for document in corpus:
            self.doc_len.append(len(document))
            frequencies: dict[str, int] = {}
            for word in document:
                frequencies[word] = frequencies.get(word, 0) + 1
            self.doc_freqs.append(frequencies)
            for word in frequencies:
                nd[word] = nd.get(word, 0) + 1

        for word, freq in nd.items():
            # Standard BM25 IDF formulation
            self.idf[word] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def get_score(self, index: int, query: list[str]) -> float:
        score = 0.0
        doc_freq = self.doc_freqs[index]
        d_len = self.doc_len[index]
        for word in query:
            if word not in doc_freq:
                continue
            freq = doc_freq[word]
            numerator = self.idf.get(word, 0.0) * freq * (self.k1 + 1)
            ratio = (self.b * d_len / self.avgdl) if self.avgdl > 0 else 0.0
            denominator = freq + self.k1 * (1 - self.b + ratio)
            score += numerator / denominator
        return score


@dataclass(slots=True)
class RetrievalResult:
    """A chunk returned by similarity or keyword search."""

    chunk: Chunk
    score: float
    rerank_score: float | None = None


class RetrievalService:
    """Retrieve relevant chunks using Vector, BM25, or Hybrid search."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def search(
        self,
        query_text: str | None = None,
        query_embedding: list[float] | None = None,
        strategy: str = "dense",
        top_k: int = 10,
        repository_id: int | None = None,
        document_id: int | None = None,
    ) -> list[RetrievalResult]:
        """Return the most relevant chunks using the specified strategy."""

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        strategy = strategy.lower()
        if strategy not in ("dense", "bm25", "hybrid"):
            raise ValueError(f"Unknown retrieval strategy: {strategy}")

        if strategy == "dense":
            if not query_embedding:
                raise ValueError("query_embedding must not be empty for dense strategy.")

            distance = Chunk.voyage_embedding.cosine_distance(
                query_embedding,
            )

            query = (
                select(
                    Chunk,
                    (1 - distance).label("score"),
                )
                .options(selectinload(Chunk.document))
                .join(Document, Chunk.document_id == Document.id)
                .where(
                    Chunk.voyage_embedding.is_not(None),
                )
            )

            if repository_id is not None:
                query = query.where(
                    Document.repository_id == repository_id,
                )

            if document_id is not None:
                query = query.where(
                    Chunk.document_id == document_id,
                )

            query = query.order_by(distance).limit(top_k)

            result = await self.db.execute(query)

            return [
                RetrievalResult(
                    chunk=chunk,
                    score=float(score),
                )
                for chunk, score in result.all()
            ]

        elif strategy == "bm25":
            if not query_text:
                raise ValueError("query_text must not be empty for bm25 strategy.")

            query = (
                select(Chunk)
                .options(selectinload(Chunk.document))
                .join(Document, Chunk.document_id == Document.id)
            )

            if repository_id is not None:
                query = query.where(
                    Document.repository_id == repository_id,
                )

            if document_id is not None:
                query = query.where(
                    Chunk.document_id == document_id,
                )

            result = await self.db.execute(query)
            chunks = list(result.scalars().all())

            if not chunks:
                return []

            corpus = [tokenize(chunk.content) for chunk in chunks]
            bm25 = BM25(corpus)
            query_tokens = tokenize(query_text)

            scored_chunks = []
            for idx, chunk in enumerate(chunks):
                score = bm25.get_score(idx, query_tokens)
                if score > 0.0:  # Only return items with a non-zero score
                    scored_chunks.append(
                        RetrievalResult(
                            chunk=chunk,
                            score=score,
                        )
                    )

            # Sort by score descending
            scored_chunks.sort(key=lambda x: x.score, reverse=True)
            return scored_chunks[:top_k]

        elif strategy == "hybrid":
            if not query_text:
                raise ValueError("query_text must not be empty for hybrid strategy.")
            if not query_embedding:
                raise ValueError("query_embedding must not be empty for hybrid strategy.")

            # Get rank lists with a wider pool of candidates
            pool_size = max(50, 2 * top_k)

            dense_results = await self.search(
                query_embedding=query_embedding,
                strategy="dense",
                top_k=pool_size,
                repository_id=repository_id,
                document_id=document_id,
            )

            bm25_results = await self.search(
                query_text=query_text,
                strategy="bm25",
                top_k=pool_size,
                repository_id=repository_id,
                document_id=document_id,
            )

            rrf_scores: dict[int, dict[str, Any]] = {}

            for rank, res in enumerate(dense_results, start=1):
                chunk_id = res.chunk.id
                if chunk_id not in rrf_scores:
                    rrf_scores[chunk_id] = {"chunk": res.chunk, "score": 0.0}
                rrf_scores[chunk_id]["score"] += 1.0 / (60.0 + rank)

            for rank, res in enumerate(bm25_results, start=1):
                chunk_id = res.chunk.id
                if chunk_id not in rrf_scores:
                    rrf_scores[chunk_id] = {"chunk": res.chunk, "score": 0.0}
                rrf_scores[chunk_id]["score"] += 1.0 / (60.0 + rank)

            sorted_rrf = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)

            return [
                RetrievalResult(
                    chunk=item["chunk"],
                    score=float(item["score"]),
                )
                for item in sorted_rrf[:top_k]
            ]
