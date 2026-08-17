from __future__ import annotations

from dataclasses import dataclass

from backend.app.db.models.chunk import Chunk
from backend.app.services.generation.base import LLMProvider
from backend.app.services.retrieval.context import ContextAssembler
from backend.app.services.retrieval.service import RetrievalService


@dataclass(slots=True)
class RAGResponse:
    """Structured response returned by the RAG orchestration pipeline."""

    answer: str
    chunks: list[Chunk]
    strategy: str
    total_chunks: int
    total_tokens: int


class RAGService:
    """Orchestrates retrieval, context assembly, and LLM response generation."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        context_assembler: ContextAssembler,
        llm_provider: LLMProvider,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.context_assembler = context_assembler
        self.llm_provider = llm_provider

    async def answer_query(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        strategy: str = "dense",
        repository_id: int | None = None,
        document_id: int | None = None,
        system_prompt: str | None = None,
    ) -> RAGResponse:
        """Retrieve context chunks, assemble context string, and generate LLM answer."""
        # Retrieval step (relying on RetrievalService's validation)
        retrieved_results = await self.retrieval_service.search(
            query_text=query,
            query_embedding=query_embedding,
            strategy=strategy,
            repository_id=repository_id,
            document_id=document_id,
        )

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
        )
