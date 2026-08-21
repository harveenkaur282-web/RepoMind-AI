import pytest
import uuid

from backend.app.db.models.monitoring import FeedbackRating
from backend.app.services.monitoring.service import MonitoringService


@pytest.mark.asyncio
async def test_record_rag_event_persists_to_db(retrieval_db) -> None:
    service = MonitoringService(retrieval_db)
    req_id = str(uuid.uuid4())
    event_data = {
        "request_id": req_id,
        "query": "What is 2+2?",
        "retrieval_strategy": "dense",
        "prompt_strategy": "concise_grounded",
        "retrieval_latency_ms": 10.5,
        "generation_latency_ms": 120.3,
        "total_latency_ms": 130.8,
        "retrieved_chunk_count": 5,
        "assembled_chunk_count": 3,
        "context_token_count": 500,
        "llm_provider": "ollama",
        "llm_model": "qwen2.5-coder:7b",
        "input_tokens": 100,
        "output_tokens": 50,
        "total_tokens": 150,
        "answer_length": 30,
        "success": True,
    }

    event = await service.record_rag_event(event_data)
    assert event.id is not None
    assert event.request_id == req_id
    assert event.success is True


@pytest.mark.asyncio
async def test_record_feedback_persists_to_db(retrieval_db) -> None:
    service = MonitoringService(retrieval_db)
    req_id = str(uuid.uuid4())

    # 1. Create a parent RAG Event first
    event_data = {
        "request_id": req_id,
        "query": "What is 2+2?",
        "retrieval_strategy": "dense",
        "prompt_strategy": "concise_grounded",
        "retrieval_latency_ms": 10.5,
        "generation_latency_ms": 120.3,
        "total_latency_ms": 130.8,
        "retrieved_chunk_count": 5,
        "assembled_chunk_count": 3,
        "context_token_count": 500,
        "llm_provider": "ollama",
        "llm_model": "qwen2.5-coder:7b",
        "answer_length": 30,
        "success": True,
    }
    await service.record_rag_event(event_data)

    # 2. Add feedback
    feedback = await service.record_feedback(
        request_id=req_id,
        rating="positive",
        feedback_text="Very helpful!",
    )

    assert feedback.id is not None
    assert feedback.rating == FeedbackRating.POSITIVE
    assert feedback.feedback_text == "Very helpful!"


