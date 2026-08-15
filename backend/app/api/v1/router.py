from fastapi import APIRouter

from backend.app.api.v1.endpoints import health, ingestion, repositories

router = APIRouter(prefix="/api/v1", tags=["API v1"])

router.include_router(health.router)
router.include_router(ingestion.router)
router.include_router(repositories.router)
