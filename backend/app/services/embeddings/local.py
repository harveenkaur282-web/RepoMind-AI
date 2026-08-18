from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from backend.app.services.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)

_MODEL_NAME = "Xenova/all-mpnet-base-v2"
_DIMENSIONS = 768


@lru_cache(maxsize=1)
def _load_onnx_model():
    """Load and cache the ONNX model and tokenizer directly on first use."""
    import onnxruntime as ort  # noqa: PLC0415
    from huggingface_hub import hf_hub_download  # noqa: PLC0415
    from transformers import AutoTokenizer  # noqa: PLC0415

    logger.info("Downloading ONNX weights directly: %s", _MODEL_NAME)
    # Download the ONNX model and tokenizer config directly from HF Hub (using Xenova's precompiled repo)
    model_path = hf_hub_download(repo_id=_MODEL_NAME, filename="onnx/model.onnx")
    tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)

    logger.info("Initializing ONNX Runtime session: %s", model_path)
    session = ort.InferenceSession(model_path)
    return session, tokenizer


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local CPU embedding provider using pure ONNX Runtime directly.

    Extremely robust, bypassing HuggingFace Optimum imports entirely to avoid
    version compatibility conflicts. Runs purely on CPU.
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

        session, tokenizer = _load_onnx_model()
        loop = asyncio.get_event_loop()

        def _encode() -> list[list[float]]:
            import numpy as np  # noqa: PLC0415

            # Tokenize the input texts
            encoded_input = tokenizer(texts, padding=True, truncation=True, return_tensors="np")

            # Prepare ONNX Runtime input bindings
            ort_inputs = {
                "input_ids": encoded_input["input_ids"].astype(np.int64),
                "attention_mask": encoded_input["attention_mask"].astype(np.int64),
            }
            if "token_type_ids" in encoded_input:
                ort_inputs["token_type_ids"] = encoded_input["token_type_ids"].astype(np.int64)

            # Run inference directly
            ort_outputs = session.run(None, ort_inputs)
            token_embeddings = ort_outputs[0]

            # Perform mean pooling
            attention_mask = encoded_input["attention_mask"]
            input_mask_expanded = np.expand_dims(attention_mask, axis=-1)
            sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
            sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)
            embeddings = sum_embeddings / sum_mask

            # Normalize embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            normalized_embeddings = embeddings / np.clip(norms, a_min=1e-9, a_max=None)

            return normalized_embeddings.tolist()

        logger.debug("Embedding %d texts with direct ONNX Runtime model", len(texts))
        return await loop.run_in_executor(None, _encode)

    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        results = await self.embed_documents([text])
        return results[0]
