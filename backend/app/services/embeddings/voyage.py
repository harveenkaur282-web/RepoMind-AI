from __future__ import annotations

import asyncio
import logging

import voyageai

from backend.app.services.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)

# Voyage AI free tier limits: 3 RPM and 10K TPM.
# To stay safely within these limits we send at most BATCH_SIZE texts per
# request and sleep SLEEP_BETWEEN_BATCHES seconds between consecutive calls.
# With BATCH_SIZE=4 and ~500 tokens per chunk, each request uses ~2K tokens,
# well under the 10K TPM cap.  22 seconds per batch gives ~2.7 RPM.
_BATCH_SIZE = 4
_SLEEP_BETWEEN_BATCHES = 22.0  # seconds


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

        all_embeddings: list[list[float]] = []
        total_batches = (len(texts) + _BATCH_SIZE - 1) // _BATCH_SIZE

        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            batch_num = i // _BATCH_SIZE + 1
            logger.info(
                "Embedding batch %d/%d (%d texts)",
                batch_num,
                total_batches,
                len(batch),
            )
            result = self.client.embed(
                batch,
                model=self.MODEL_NAME,
                input_type="document",
            )
            all_embeddings.extend(result.embeddings)

            # Sleep between batches to respect the 3 RPM free-tier limit.
            # Skip the sleep after the final batch.
            if i + _BATCH_SIZE < len(texts):
                logger.debug("Rate-limit sleep %.0fs before next batch", _SLEEP_BETWEEN_BATCHES)
                await asyncio.sleep(_SLEEP_BETWEEN_BATCHES)

        return all_embeddings

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
