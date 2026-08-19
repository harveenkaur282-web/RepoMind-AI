from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from backend.app.services.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)

_MODEL_PATH = Path("backend/app/models/Xenova/all-mpnet-base-v2")
_DIMENSIONS = 768


@lru_cache(maxsize=1)
def _load_onnx_embedder():
    """Initializes the tokenizer and ONNX inference session."""
    logger.info("Initializing native ONNX session from: %s", _MODEL_PATH)
    tokenizer = Tokenizer.from_file(str(_MODEL_PATH / "tokenizer.json"))
    session = ort.InferenceSession(str(_MODEL_PATH / "model.onnx"))
    input_names = {inp.name for inp in session.get_inputs()}
    return session, tokenizer, input_names


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local CPU embedding provider using pure ONNX Runtime and tokenizers.

    Bypasses PyTorch, HuggingFace transformers, and Optimum wrappers entirely
    following the custom Zoomcamp implementation.
    """

    MODEL_NAME = "Xenova/all-mpnet-base-v2"
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

        session, tokenizer, input_names = _load_onnx_embedder()
        loop = asyncio.get_event_loop()

        def _encode() -> list[list[float]]:
            tokenizer.enable_padding()
            encoded = tokenizer.encode_batch(texts)

            feed = {}
            if "input_ids" in input_names:
                feed["input_ids"] = np.array([e.ids for e in encoded], dtype=np.int64)
            if "attention_mask" in input_names:
                feed["attention_mask"] = np.array(
                    [e.attention_mask for e in encoded], dtype=np.int64
                )
            if "token_type_ids" in input_names:
                feed["token_type_ids"] = np.array([e.type_ids for e in encoded], dtype=np.int64)

            # Execute ONNX graph
            hidden = session.run(None, feed)[0]
            mask = feed["attention_mask"][..., None]

            # Mean Pooling
            pooled = (hidden * mask).sum(axis=1) / mask.sum(axis=1)

            # L2 Normalization (cosine similarity compatibility)
            norms = np.linalg.norm(pooled, axis=1, keepdims=True)
            normalized = pooled / np.clip(norms, a_min=1e-9, a_max=None)

            return normalized.tolist()

        logger.debug("Embedding %d texts with native ONNX model", len(texts))
        return await loop.run_in_executor(None, _encode)

    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        results = await self.embed_documents([text])
        return results[0]
