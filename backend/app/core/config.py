from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RepoMind AI"
    environment: str = "development"
    debug: bool = True

    database_url: str
    redis_url: str

    github_token: str | None = None

    llm_provider: str | None = None
    llm_api_key: str | None = None

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "BAAI/bge-reranker-base"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()