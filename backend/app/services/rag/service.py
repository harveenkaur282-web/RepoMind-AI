from __future__ import annotations

from dataclasses import dataclass

from backend.app.db.models.chunk import Chunk
from backend.app.services.generation.base import LLMProvider
from backend.app.services.rag.reranker import Reranker
from backend.app.services.retrieval.context import ContextAssembler
from backend.app.services.retrieval.service import RetrievalResult, RetrievalService


@dataclass(slots=True)
class RAGResponse:
    """Structured response returned by the RAG orchestration pipeline."""

    answer: str
    chunks: list[Chunk]
    strategy: str
    total_chunks: int
    total_tokens: int
    prompt_strategy: str = "concise_grounded"
    rewritten_query: str | None = None
    results: list[RetrievalResult] | None = None


class RAGService:
    """Orchestrates retrieval, context assembly, and LLM response generation."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        context_assembler: ContextAssembler,
        llm_provider: LLMProvider,
        reranker: Reranker | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.context_assembler = context_assembler
        self.llm_provider = llm_provider
        self.reranker = reranker

    async def answer_query(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        strategy: str = "dense",
        repository_id: int | None = None,
        document_id: int | None = None,
        system_prompt: str | None = None,
        prompt_strategy: str = "concise_grounded",
        search_query: str | None = None,
        rerank: bool = False,
        rerank_limit: int = 20,
    ) -> RAGResponse:
        """Retrieve context chunks, assemble context string, and generate LLM answer."""
        retrieval_query = search_query if search_query is not None else query

        # Retrieve a larger candidate pool if reranking is enabled
        retrieve_top_k = rerank_limit if (rerank and self.reranker) else 10

        # Retrieval step (relying on RetrievalService's validation)
        retrieved_results = await self.retrieval_service.search(
            query_text=retrieval_query,
            query_embedding=query_embedding,
            strategy=strategy,
            repository_id=repository_id,
            document_id=document_id,
            top_k=retrieve_top_k,
        )

        # Reranking step
        if rerank and self.reranker:
            retrieved_results = await self.reranker.rerank(
                query=retrieval_query,
                candidates=retrieved_results,
            )
            # Slice back to original target top_k (10)
            retrieved_results = retrieved_results[:10]

        # Context assembly step
        assembled_context = self.context_assembler.assemble(retrieved_results)

        # Response generation step
        answer = await self.llm_provider.generate(
            context=assembled_context.context_str,
            query=query,
            system_prompt=system_prompt,
        )

        return RAGResponse(
            answer=answer,
            chunks=assembled_context.chunks,
            strategy=strategy,
            total_chunks=assembled_context.total_chunks,
            total_tokens=assembled_context.total_tokens,
            prompt_strategy=prompt_strategy,
            rewritten_query=search_query,
            results=retrieved_results,
        )
