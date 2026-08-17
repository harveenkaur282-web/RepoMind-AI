from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.dependencies import get_db
from backend.app.services.embeddings.service import EmbeddingService
from backend.app.services.embeddings.voyage import VoyageEmbeddingProvider
from backend.app.services.generation.ollama import OllamaProvider
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
            embedding_service = EmbeddingService(db=db, provider=provider)
            query_embedding = await embedding_service.embed_query(query)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate query embedding: {exc}",
            ) from exc

    # 2. Setup services
    retrieval_service = RetrievalService(db=db)
    context_assembler = ContextAssembler()
    llm_provider = OllamaProvider(
        base_url=settings.ollama_url,
        model=settings.ollama_model,
    )

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
