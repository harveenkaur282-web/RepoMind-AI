from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from backend.app.services.rag.reranker.base import Reranker
from backend.app.services.retrieval.service import RetrievalResult

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parents[5]
_MODEL_PATH = _BASE_DIR / "backend/app/models/Xenova/bge-reranker-base"


@lru_cache(maxsize=1)
def _load_onnx_reranker():
    logger.info("Initializing neural cross-encoder ONNX session from: %s", _MODEL_PATH)
    tokenizer = Tokenizer.from_file(str(_MODEL_PATH / "tokenizer.json"))
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(str(_MODEL_PATH / "model.onnx"), opts)
    input_names = {inp.name for inp in session.get_inputs()}
    return session, tokenizer, input_names


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


class ONNXCrossEncoderReranker(Reranker):
    """Real Neural Cross-Encoder Reranker using BAAI/bge-reranker-base ONNX weights."""

    def __init__(self, model_name: str = "Xenova/bge-reranker-base") -> None:
        self.model_name = model_name

    async def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        if not candidates:
            return []

        session, tokenizer, input_names = _load_onnx_reranker()
        loop = asyncio.get_event_loop()

        def _score_candidates() -> list[RetrievalResult]:
            # Construct text pairs: (query, candidate_chunk_text)
            pairs = []
            for c in candidates:
                chunk_text = c.chunk.content
                if c.chunk.document and c.chunk.document.path:
                    chunk_text = f"File: {c.chunk.document.path}\n{chunk_text}"
                pairs.append((query, chunk_text[:1000]))

            tokenizer.enable_padding()
            tokenizer.enable_truncation(max_length=256)

            encoded = tokenizer.encode_batch(pairs)

            feed = {}
            if "input_ids" in input_names:
                feed["input_ids"] = np.array([e.ids for e in encoded], dtype=np.int64)
            if "attention_mask" in input_names:
                feed["attention_mask"] = np.array(
                    [e.attention_mask for e in encoded], dtype=np.int64
                )
            if "token_type_ids" in input_names:
                feed["token_type_ids"] = np.array([e.type_ids for e in encoded], dtype=np.int64)

            outputs = session.run(None, feed)
            logits = outputs[0].squeeze(-1) if len(outputs[0].shape) > 1 else outputs[0]
            scores = _sigmoid(logits).tolist()

            if isinstance(scores, float):
                scores = [scores]

            for candidate, score in zip(candidates, scores, strict=False):
                candidate.rerank_score = float(score)

            # Sort descending by neural rerank score
            sorted_candidates = sorted(
                candidates, key=lambda x: x.rerank_score or 0.0, reverse=True
            )
            return sorted_candidates

        return await loop.run_in_executor(None, _score_candidates)
