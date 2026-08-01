from fastapi import FastAPI

from backend.app.api.v1.router import router as api_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Agentic Repository Intelligence Workspace for GitHub Knowledge Discovery",
    version="0.1.0",
)


app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Hello, this is RepoMind AI!",
        "version": "0.1.0",
    }