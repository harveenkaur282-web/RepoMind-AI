from fastapi import APIRouter

from backend.app.api.v1.endpoints import health, ingestion, rag, repositories, feedback

router = APIRouter(prefix="/api/v1", tags=["API v1"])

router.include_router(health.router)
router.include_router(ingestion.router)
router.include_router(repositories.router)
router.include_router(rag.router)
router.include_router(feedback.router)
