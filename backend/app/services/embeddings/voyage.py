from __future__ import annotations

import voyageai

from backend.app.services.embeddings.base import EmbeddingProvider


class VoyageEmbeddingProvider(EmbeddingProvider):
    """Voyage AI embedding provider for code retrieval."""

    MODEL_NAME = "voyage-code-3"
    DIMENSIONS = 1024

    def __init__(self, api_key: str | None = None) -> None:
        self.client = voyageai.Client(api_key=api_key)

    @property
    def model_name(self) -> str:
        return self.MODEL_NAME

    @property
    def dimensions(self) -> int:
        return self.DIMENSIONS

    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        result = self.client.embed(
            texts,
            model=self.MODEL_NAME,
            input_type="document",
        )
        return result.embeddings

    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        result = self.client.embed(
            [text],
            model=self.MODEL_NAME,
            input_type="query",
        )
        return result.embeddings[0]
