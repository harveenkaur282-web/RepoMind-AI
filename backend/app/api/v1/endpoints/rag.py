from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.dependencies import get_db
from backend.app.services.embeddings.local import LocalEmbeddingProvider
from backend.app.services.generation.factory import get_llm_provider
from backend.app.services.rag.prompts import get_system_prompt
from backend.app.services.rag.reranker import LocalCrossEncoderReranker
from backend.app.services.rag.rewriter import QueryRewriter
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
    prompt_strategy: str = "concise_grounded",
    rewrite_query: bool = False,
    rerank: bool | None = None,
    rerank_limit: int | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict[str, object]:
    settings = get_settings()

    try:
        llm_provider = get_llm_provider(settings)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    search_query = None
    if rewrite_query:
        try:
            rewriter = QueryRewriter(llm_provider)
            search_query = await rewriter.rewrite(query)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Query rewriting failed: {exc}",
            ) from exc

    query_to_embed = search_query if search_query is not None else query

    # 1. Get embedding for query if strategy needs it
    query_embedding = None
    if strategy in ("dense", "hybrid"):
        try:
            provider = LocalEmbeddingProvider()
            query_embedding = await provider.embed_query(query_to_embed)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate query embedding: {exc}",
            ) from exc

    # 2. Setup services
    retrieval_service = RetrievalService(db=db)
    context_assembler = ContextAssembler()

    try:
        system_prompt = get_system_prompt(prompt_strategy)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Resolve reranker settings
    use_rerank = rerank if rerank is not None else settings.reranker_enabled
    use_limit = rerank_limit if rerank_limit is not None else settings.reranker_limit

    reranker = None
    if use_rerank:
        reranker = LocalCrossEncoderReranker(model_name=settings.reranker_model)

    rag_service = RAGService(
        retrieval_service=retrieval_service,
        context_assembler=context_assembler,
        llm_provider=llm_provider,
        reranker=reranker,
    )

    try:
        response: RAGResponse = await rag_service.answer_query(
            query=query,
            query_embedding=query_embedding,
            strategy=strategy,
            repository_id=repository_id,
            document_id=document_id,
            system_prompt=system_prompt,
            prompt_strategy=prompt_strategy,
            search_query=search_query,
            rerank=use_rerank,
            rerank_limit=use_limit,
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
                "id": res.chunk.id if hasattr(res, "chunk") else res.id,
                "content": res.chunk.content if hasattr(res, "chunk") else res.content,
                "document_path": (
                    (res.chunk.document.path if res.chunk.document else "Unknown")
                    if hasattr(res, "chunk")
                    else (res.document.path if res.document else "Unknown")
                ),
                "score": getattr(res, "score", None),
                "rerank_score": getattr(res, "rerank_score", None),
            }
            for res in (response.results if response.results is not None else response.chunks)
        ],
        "strategy": response.strategy,
        "total_chunks": response.total_chunks,
        "total_tokens": response.total_tokens,
        "prompt_strategy": response.prompt_strategy,
        "rewritten_query": response.rewritten_query,
    }


@router.post("/compare")
async def compare_retrieval(
    query: str,
    repository_id: int | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict[str, list[dict[str, object]]]:
    get_settings()
    retrieval_service = RetrievalService(db=db)

    query_embedding = None
    try:
        provider = LocalEmbeddingProvider()
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
