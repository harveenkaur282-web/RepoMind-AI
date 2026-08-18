from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class FeedbackRating(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class RAGEvent(Base):
    __tablename__ = "rag_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )
    query: Mapped[str] = mapped_column(Text)
    retrieval_strategy: Mapped[str] = mapped_column(String(50), index=True)
    prompt_strategy: Mapped[str] = mapped_column(String(50))
    retrieval_latency_ms: Mapped[float] = mapped_column(Float)
    generation_latency_ms: Mapped[float] = mapped_column(Float)
    total_latency_ms: Mapped[float] = mapped_column(Float)
    retrieved_chunk_count: Mapped[int] = mapped_column(Integer)
    assembled_chunk_count: Mapped[int] = mapped_column(Integer)
    context_token_count: Mapped[int] = mapped_column(Integer)
    llm_provider: Mapped[str] = mapped_column(String(50))
    llm_model: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answer_length: Mapped[int] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    repository_id: Mapped[int | None] = mapped_column(
        ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True
    )

    feedbacks: Mapped[list["UserFeedback"]] = relationship(
        back_populates="rag_event", cascade="all, delete-orphan"
    )


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rag_events.request_id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[FeedbackRating] = mapped_column(String(20))
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )

    rag_event: Mapped["RAGEvent"] = relationship(back_populates="feedbacks")
