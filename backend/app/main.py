from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.v1.router import router as api_router
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging, get_logger

configure_logging()

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_starting")

    # Future:
    # - Initialize PostgreSQL
    # - Connect Redis
    # - Load embedding model
    # - Start workers

    yield

    logger.info("application_shutting_down")


app = FastAPI(
    title=settings.app_name,
    description="Agentic Repository Intelligence Workspace for GitHub Knowledge Discovery",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Hello, this is RepoMind AI!",
        "version": "0.1.0",
    }