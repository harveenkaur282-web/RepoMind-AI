import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.dependencies import get_db
from backend.app.services.monitoring.service import MonitoringService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackCreate(BaseModel):
    request_id: str = Field(..., description="UUID of the RAG request")
    rating: str = Field(..., description="'positive' or 'negative'")
    feedback_text: str | None = Field(None, description="Optional textual user feedback")


class FeedbackResponse(BaseModel):
    id: int
    request_id: str
    rating: str
    feedback_text: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_feedback(
    payload: FeedbackCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Post user satisfaction feedback on a completed RAG request."""
    if payload.rating not in ("positive", "negative"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rating must be 'positive' or 'negative'",
        )

    try:
        service = MonitoringService(db)
        feedback = await service.record_feedback(
            request_id=payload.request_id,
            rating=payload.rating,
            feedback_text=payload.feedback_text,
        )
        return feedback
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {exc}",
        ) from exc
