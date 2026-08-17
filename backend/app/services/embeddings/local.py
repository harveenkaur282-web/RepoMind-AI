from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from backend.app.services.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)

_MODEL_NAME = "nomic-ai/nomic-embed-code"
_DIMENSIONS = 768


@lru_cache(maxsize=1)
def _load_model():
    """Load and cache the sentence-transformers model on first use."""
    from sentence_transformers import SentenceTransformer  # noqa: PLC0415

    logger.info("Loading local embedding model: %s", _MODEL_NAME)
    model = SentenceTransformer(_MODEL_NAME, trust_remote_code=True)
    logger.info("Local embedding model loaded.")
    return model


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local CPU embedding provider using nomic-ai/nomic-embed-code via sentence-transformers.

    No API key or rate limit. Model is downloaded once and cached in the
    sentence-transformers cache directory (~/.cache/huggingface/hub).
    Inference runs in a thread-pool executor so it does not block the async
    event loop.
    """

    MODEL_NAME = _MODEL_NAME
    DIMENSIONS = _DIMENSIONS

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

        model = _load_model()
        loop = asyncio.get_event_loop()

        def _encode() -> list[list[float]]:
            embeddings = model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return [emb.tolist() for emb in embeddings]

        logger.debug("Embedding %d texts with local model", len(texts))
        return await loop.run_in_executor(None, _encode)

    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        results = await self.embed_documents([text])
        return results[0]
