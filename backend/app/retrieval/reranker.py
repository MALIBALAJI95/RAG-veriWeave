"""Cross-encoder reranking component for fine-grained relevance scoring."""

import math
from typing import List, Optional
from backend.app.core.logging import get_logger
from backend.app.schemas.chat import RetrievedChunk

logger = get_logger(__name__)


def sigmoid(x: float) -> float:
    """Compute numerical sigmoid with clipping to prevent overflow."""
    if x < -20.0:
        return 0.0
    if x > 20.0:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


class CrossEncoderReranker:
    """Reranks retrieved candidate chunks using a pretrained Cross-Encoder model."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",
        enabled: bool = True,
    ):
        self.model_name = model_name
        self.device = device
        self.enabled = enabled
        self._model = None
        self._load_failed = False

    def _get_model(self):
        """Lazy load CrossEncoder from local cache."""
        if not self.enabled or self._load_failed:
            return None

        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder

                logger.info(f"Loading CrossEncoder '{self.model_name}' on device '{self.device}'...")
                try:
                    self._model = CrossEncoder(
                        self.model_name,
                        device=self.device,
                        local_files_only=True,
                    )
                except Exception:
                    self._model = CrossEncoder(
                        self.model_name,
                        device=self.device,
                        local_files_only=False,
                    )
                logger.info("CrossEncoder loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load CrossEncoder '{self.model_name}': {e}. Reranking will be bypassed.")
                self._load_failed = True
                self._model = None

        return self._model

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int = 4,
    ) -> List[RetrievedChunk]:
        """Compute cross-attention relevance scores for (query, document) pairs and re-sort."""
        if not chunks or not self.enabled:
            return chunks[:top_k]

        model = self._get_model()
        if model is None:
            # Fallback if cross-encoder disabled or unavailable
            return chunks[:top_k]

        pairs = [(query, c.text) for c in chunks]

        try:
            raw_scores = model.predict(pairs, show_progress_bar=False)

            scored_candidates = []
            for idx, chunk in enumerate(chunks):
                raw_score = float(raw_scores[idx])
                # Convert logits to probability via sigmoid
                norm_score = round(sigmoid(raw_score), 4)

                clone = chunk.model_copy(deep=True)
                clone.rerank_score = norm_score
                clone.metadata = {
                    **clone.metadata,
                    "raw_cross_encoder_logit": round(raw_score, 4),
                    "pre_rerank_score": clone.score,
                    "pre_rerank_rank": clone.original_rank,
                }
                # Update score with reranked score
                clone.score = norm_score
                clone.retrieval_method = f"{clone.retrieval_method}+rerank"
                scored_candidates.append(clone)

            # Sort descending by cross-encoder score
            scored_candidates.sort(key=lambda c: (c.rerank_score or 0.0), reverse=True)

            # Re-assign 1-based ranks
            for new_rank, c in enumerate(scored_candidates[:top_k], 1):
                c.original_rank = new_rank

            logger.info(f"Cross-encoder reranked {len(chunks)} candidates -> returning top {top_k}")
            return scored_candidates[:top_k]
        except Exception as e:
            logger.error(f"Error during cross-encoder reranking: {e}")
            return chunks[:top_k]
