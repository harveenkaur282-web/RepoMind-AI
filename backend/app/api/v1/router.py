from fastapi import APIRouter

from backend.app.api.v1.endpoints import health

router = APIRouter()

router.include_router(
    health.router,
)