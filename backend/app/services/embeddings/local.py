from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from backend.app.services.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)

_MODEL_NAME = "nomic-ai/nomic-embed-code"
_DIMENSIONS = 768


@lru_cache(maxsize=1)
def _load_onnx_model():
    """Load and cache the Optimum ONNX model and tokenizer on first use."""
    from optimum.onnxruntime import ORTModelForFeatureExtraction  # noqa: PLC0415
    from transformers import AutoTokenizer  # noqa: PLC0415

    logger.info("Loading Optimum ONNX model: %s", _MODEL_NAME)
    # This automatically downloads and exports the model to ONNX format (or uses cache)
    tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
    model = ORTModelForFeatureExtraction.from_pretrained(
        _MODEL_NAME, export=True, provider="CPUExecutionProvider"
    )
    logger.info("Optimum ONNX model and tokenizer loaded.")
    return model, tokenizer


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local CPU embedding provider using ONNX Runtime via HuggingFace Optimum.

    Extremely lightweight, requires no PyTorch dependencies, and uses very little
    RAM. Works purely on CPU with no API keys or rate limits.
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

        model, tokenizer = _load_onnx_model()
        loop = asyncio.get_event_loop()

        def _encode() -> list[list[float]]:
            import numpy as np  # noqa: PLC0415

            # Tokenize the input texts
            encoded_input = tokenizer(texts, padding=True, truncation=True, return_tensors="np")

            # Run inference on ONNX Runtime
            model_output = model(**encoded_input)

            # Perform mean pooling
            token_embeddings = model_output[0]  # First element of tuple contains hidden state
            attention_mask = encoded_input["attention_mask"]

            input_mask_expanded = np.expand_dims(attention_mask, axis=-1)
            sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
            sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)
            embeddings = sum_embeddings / sum_mask

            # Normalize embeddings to unit length (cosine similarity)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            normalized_embeddings = embeddings / np.clip(norms, a_min=1e-9, a_max=None)

            return normalized_embeddings.tolist()

        logger.debug("Embedding %d texts with ONNX Runtime model", len(texts))
        return await loop.run_in_executor(None, _encode)

    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        results = await self.embed_documents([text])
        return results[0]
