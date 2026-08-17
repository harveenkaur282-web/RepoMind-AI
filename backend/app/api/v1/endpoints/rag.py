from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.dependencies import get_db
from backend.app.services.embeddings.voyage import VoyageEmbeddingProvider
from backend.app.services.generation.factory import get_llm_provider
from backend.app.services.rag.service import RAGResponse, RAGService
from backend.app.services.retrieval.context import ContextAssembler
from backend.app.services.retrieval.service import RetrievalService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query")
async def query_rag(
    query: str,
    strategy: str = "dense",
    repository_id: int | None = None,
    document_id: int | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict[str, object]:
    settings = get_settings()

    # 1. Get embedding for query if strategy needs it
    query_embedding = None
    if strategy in ("dense", "hybrid"):
        try:
            provider = VoyageEmbeddingProvider(api_key=settings.voyage_api_key)
            query_embedding = await provider.embed_query(query)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate query embedding: {exc}",
            ) from exc

    # 2. Setup services
    retrieval_service = RetrievalService(db=db)
    context_assembler = ContextAssembler()
    try:
        llm_provider = get_llm_provider(settings)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    rag_service = RAGService(
        retrieval_service=retrieval_service,
        context_assembler=context_assembler,
        llm_provider=llm_provider,
    )

    try:
        response: RAGResponse = await rag_service.answer_query(
            query=query,
            query_embedding=query_embedding,
            strategy=strategy,
            repository_id=repository_id,
            document_id=document_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"RAG query failed: {exc}",
        ) from exc

    return {
        "answer": response.answer,
        "chunks": [
            {
                "id": chunk.id,
                "content": chunk.content,
                "document_path": chunk.document.path if chunk.document else "Unknown",
            }
            for chunk in response.chunks
        ],
        "strategy": response.strategy,
        "total_chunks": response.total_chunks,
        "total_tokens": response.total_tokens,
    }


@router.post("/compare")
async def compare_retrieval(
    query: str,
    repository_id: int | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict[str, list[dict[str, object]]]:
    settings = get_settings()
    retrieval_service = RetrievalService(db=db)

    query_embedding = None
    try:
        provider = VoyageEmbeddingProvider(api_key=settings.voyage_api_key)
        query_embedding = await provider.embed_query(query)
    except Exception:
        pass

    results = {}
    strategies = ["dense", "bm25", "hybrid"]
    for strategy in strategies:
        if strategy == "dense" and query_embedding is None:
            results[strategy] = []
            continue
        try:
            hits = await retrieval_service.search(
                query_text=query,
                query_embedding=query_embedding if strategy in ("dense", "hybrid") else None,
                strategy=strategy,
                repository_id=repository_id,
                top_k=5,
            )
            results[strategy] = [
                {
                    "content": hit.chunk.content,
                    "document_path": hit.chunk.document.path if hit.chunk.document else "Unknown",
                    "score": hit.score,
                }
                for hit in hits
            ]
        except Exception as exc:
            results[strategy] = [{"error": str(exc)}]

    return results
