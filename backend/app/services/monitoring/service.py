import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.monitoring import RAGEvent, UserFeedback

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service to record RAG event metrics and user feedback directly to PostgreSQL."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_rag_event(self, event_data: dict[str, Any]) -> RAGEvent:
        """Create and store a RAG execution trace log event."""
        try:
            # Simple credential filtering/obfuscation from query texts
            query = event_data.get("query", "")
            # Basic sanitization of API-like strings if they appear in queries
            for secret_key in ["sk-", "ghp_", "voyage-"]:
                if secret_key in query:
                    query = "[REDACTED SENSITIVE QUERY CONTENT]"
                    break

            event = RAGEvent(
                request_id=event_data["request_id"],
                query=query,
                retrieval_strategy=event_data["retrieval_strategy"],
                prompt_strategy=event_data["prompt_strategy"],
                retrieval_latency_ms=event_data["retrieval_latency_ms"],
                generation_latency_ms=event_data["generation_latency_ms"],
                total_latency_ms=event_data["total_latency_ms"],
                retrieved_chunk_count=event_data["retrieved_chunk_count"],
                assembled_chunk_count=event_data["assembled_chunk_count"],
                context_token_count=event_data["context_token_count"],
                llm_provider=event_data["llm_provider"],
                llm_model=event_data["llm_model"],
                input_tokens=event_data.get("input_tokens"),
                output_tokens=event_data.get("output_tokens"),
                total_tokens=event_data.get("total_tokens"),
                answer_length=event_data["answer_length"],
                success=event_data.get("success", True),
                error_message=event_data.get("error_message"),
                repository_id=event_data.get("repository_id"),
            )
            self.db.add(event)
            await self.db.commit()
            logger.info("Recorded RAGEvent trace with request_id: %s", event.request_id)
            return event
        except Exception as exc:
            await self.db.rollback()
            logger.error("Failed to record RAG event: %s", exc, exc_info=True)
            raise

    async def record_feedback(
        self, request_id: str, rating: str, feedback_text: str | None = None
    ) -> UserFeedback:
        """Store a user thumbs-up/down review linked to a specific RAG execution trace."""
        try:
            # Verify the event exists first
            event_check = await self.db.execute(
                select(RAGEvent).where(RAGEvent.request_id == request_id)
            )
            event = event_check.scalar_one_or_none()
            if not event:
                raise ValueError(f"RAG event with request_id {request_id} does not exist.")

            feedback = UserFeedback(
                request_id=request_id,
                rating=rating,
                feedback_text=feedback_text,
            )
            self.db.add(feedback)
            await self.db.commit()
            logger.info("Recorded user feedback for request_id: %s", request_id)
            return feedback
        except Exception as exc:
            await self.db.rollback()
            logger.error("Failed to record user feedback: %s", exc, exc_info=True)
            raise
