from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RepoMind AI"
    environment: str = "development"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://repomind:repomind@localhost:5432/repomind"
    redis_url: str | None = None

    github_token: str | None = None

    llm_provider: str = "ollama"
    llm_api_key: str | None = None

    voyage_api_key: str | None = None
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    openrouter_api_key: str | None = None
    openrouter_model: str = "meta-llama/llama-3-8b-instruct:free"

    embedding_model: str = "Xenova/bge-base-en-v1.5"
    reranker_model: str = "Xenova/bge-reranker-base"
    reranker_enabled: bool = False
    reranker_limit: int = 20

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
