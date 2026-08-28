import time
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.dependencies import get_db
from backend.app.db.session import AsyncSessionLocal
from backend.app.services.embeddings.local import LocalEmbeddingProvider
from backend.app.services.generation.factory import get_llm_provider
from backend.app.services.monitoring.service import MonitoringService
from backend.app.services.rag.prompts import get_system_prompt
from backend.app.services.rag.reranker import ONNXCrossEncoderReranker
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
    llm_provider: str | None = None,
    llm_model: str | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    background_tasks: BackgroundTasks = None,
) -> dict[str, object]:
    start_total_time = time.perf_counter()
    request_id = str(uuid4())
    settings = get_settings()

    # Apply optional LLM provider overrides dynamically
    override_settings = settings
    if llm_provider or llm_model:
        from backend.app.core.config import Settings

        override_settings = Settings(**settings.model_dump())
        if llm_provider:
            override_settings.llm_provider = llm_provider
        if llm_model:
            provider_key = llm_provider if llm_provider else settings.llm_provider
            provider_key = provider_key.lower()
            if provider_key == "groq":
                override_settings.groq_model = llm_model
            elif provider_key == "gemini":
                override_settings.gemini_model = llm_model
            elif provider_key == "openrouter":
                override_settings.openrouter_model = llm_model
            elif provider_key == "ollama":
                override_settings.ollama_model = llm_model

    try:
        llm_provider_instance = get_llm_provider(override_settings)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    search_query = None
    if rewrite_query:
        try:
            rewriter = QueryRewriter(llm_provider_instance)
            search_query = await rewriter.rewrite(query)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Query rewriting failed: {exc}",
            ) from exc

    query_to_embed = search_query if search_query is not None else query

    # 1. Get embedding for query if strategy needs it
    query_embedding = None
    start_retrieval_time = time.perf_counter()
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
        reranker = ONNXCrossEncoderReranker(model_name=settings.reranker_model)

    rag_service = RAGService(
        retrieval_service=retrieval_service,
        context_assembler=context_assembler,
        llm_provider=llm_provider_instance,
        reranker=reranker,
    )

    try:
        # Perform retrieval
        await retrieval_service.search(
            query_text=query_to_embed,
            query_embedding=query_embedding,
            strategy=strategy,
            repository_id=repository_id,
            document_id=document_id,
            top_k=use_limit if use_rerank else 10,
        )
        retrieval_latency = time.perf_counter() - start_retrieval_time

        # Perform generation
        start_generation_time = time.perf_counter()
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
        generation_latency = time.perf_counter() - start_generation_time
    except Exception as exc:
        total_latency = time.perf_counter() - start_total_time
        # Record failure event in background
        if background_tasks:
            llm_model = (
                override_settings.groq_model
                if override_settings.llm_provider == "groq"
                else (
                    override_settings.gemini_model
                    if override_settings.llm_provider == "gemini"
                    else (
                        override_settings.openrouter_model
                        if override_settings.llm_provider == "openrouter"
                        else override_settings.ollama_model
                    )
                )
            )
            error_data = {
                "request_id": request_id,
                "query": query,
                "retrieval_strategy": strategy,
                "prompt_strategy": prompt_strategy,
                "retrieval_latency_ms": 0.0,
                "generation_latency_ms": 0.0,
                "total_latency_ms": total_latency * 1000,
                "retrieved_chunk_count": 0,
                "assembled_chunk_count": 0,
                "context_token_count": 0,
                "llm_provider": override_settings.llm_provider,
                "llm_model": llm_model,
                "answer_length": 0,
                "success": False,
                "error_message": str(exc),
                "repository_id": repository_id,
            }

            async def log_error_event():
                async with AsyncSessionLocal() as session:
                    monitor = MonitoringService(session)
                    await monitor.record_rag_event(error_data)

            background_tasks.add_task(log_error_event)

        raise HTTPException(
            status_code=500,
            detail=f"RAG query failed: {exc}",
        ) from exc

    total_latency = time.perf_counter() - start_total_time

    # Record success event in background
    if background_tasks:
        # Resolve metrics
        retrieved_count = (
            len(response.results) if response.results is not None else len(response.chunks)
        )
        assembled_count = response.total_chunks

        # Token details (input/output are optional LLM attributes)
        input_tokens = getattr(response, "input_tokens", None)
        output_tokens = getattr(response, "output_tokens", None)
        total_toks = response.total_tokens

        llm_model = (
            override_settings.groq_model
            if override_settings.llm_provider == "groq"
            else (
                override_settings.gemini_model
                if override_settings.llm_provider == "gemini"
                else (
                    override_settings.openrouter_model
                    if override_settings.llm_provider == "openrouter"
                    else override_settings.ollama_model
                )
            )
        )
        event_data = {
            "request_id": request_id,
            "query": query,
            "retrieval_strategy": strategy,
            "prompt_strategy": prompt_strategy,
            "retrieval_latency_ms": retrieval_latency * 1000,
            "generation_latency_ms": generation_latency * 1000,
            "total_latency_ms": total_latency * 1000,
            "retrieved_chunk_count": retrieved_count,
            "assembled_chunk_count": assembled_count,
            "context_token_count": total_toks,
            "llm_provider": override_settings.llm_provider,
            "llm_model": llm_model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_toks,
            "answer_length": len(response.answer),
            "answer": response.answer,
            "success": True,
            "repository_id": repository_id,
        }

        async def log_success_event():
            async with AsyncSessionLocal() as session:
                monitor = MonitoringService(session)
                await monitor.record_rag_event(event_data)

        background_tasks.add_task(log_success_event)

    return {
        "request_id": request_id,
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


@router.get("/history")
async def get_history(
    repository_id: int | None = None,
    limit: int = 20,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[dict[str, object]]:
    from sqlalchemy import select

    from backend.app.db.models.monitoring import RAGEvent

    query_select = (
        select(RAGEvent)
        .where(RAGEvent.success.is_(True))
        .order_by(RAGEvent.created_at.desc())
        .limit(limit)
    )

    if repository_id is not None:
        query_select = query_select.where(RAGEvent.repository_id == repository_id)

    result = await db.execute(query_select)
    events = result.scalars().all()

    return [
        {
            "request_id": event.request_id,
            "query": event.query,
            "answer": event.answer,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "strategy": event.retrieval_strategy,
        }
        for event in events
    ]
