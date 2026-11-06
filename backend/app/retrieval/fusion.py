"""Reciprocal Rank Fusion (RRF) algorithm for multi-strategy and multi-query retrieval."""

from typing import Any, Dict, List, Optional
from backend.app.core.logging import get_logger
from backend.app.schemas.chat import RetrievedChunk

logger = get_logger(__name__)


class RRFFusionEngine:
    """Combines multiple ranked candidate lists using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF_Score(d) = sum_{r in Rankings} ( 1.0 / (k + rank_r(d)) )
    """

    def __init__(self, k: int = 60):
        if k <= 0:
            raise ValueError(f"RRF smoothing parameter k must be positive, got {k}")
        self.k = k

    def fuse(
        self,
        ranked_lists: List[List[RetrievedChunk]],
        top_k: int = 4,
        source_labels: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        """Fuse multiple ranked lists of chunks, handling duplicates and preserving score provenance."""
        if not ranked_lists:
            return []

        # Map chunk_id to accumulated RRF score and chunk representation
        fused_scores: Dict[str, float] = {}
        chunk_map: Dict[str, RetrievedChunk] = {}
        provenance_map: Dict[str, Dict[str, Any]] = {}

        for list_idx, chunk_list in enumerate(ranked_lists):
            label = source_labels[list_idx] if source_labels and list_idx < len(source_labels) else f"rank_list_{list_idx}"
            for rank_0, chunk in enumerate(chunk_list):
                rank = rank_0 + 1  # 1-based rank
                chunk_id = chunk.chunk_id
                rrf_term = 1.0 / (self.k + rank)

                fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + rrf_term

                if chunk_id not in chunk_map:
                    # Clone chunk to avoid mutating inputs
                    chunk_map[chunk_id] = chunk.model_copy(deep=True)
                    provenance_map[chunk_id] = {
                        "ranks": {label: rank},
                        "original_scores": {label: round(chunk.score, 4)},
                    }
                else:
                    provenance_map[chunk_id]["ranks"][label] = rank
                    provenance_map[chunk_id]["original_scores"][label] = round(chunk.score, 4)

        # Sort chunk IDs by descending accumulated RRF score
        sorted_chunk_ids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)

        results: List[RetrievedChunk] = []
        for final_rank, cid in enumerate(sorted_chunk_ids[:top_k], 1):
            c = chunk_map[cid]
            c.score = round(fused_scores[cid], 5)
            c.original_rank = final_rank
            c.retrieval_method = "rrf_fusion"
            c.metadata = {
                **c.metadata,
                "rrf_score": round(fused_scores[cid], 5),
                "rrf_ranks": provenance_map[cid]["ranks"],
                "rrf_source_scores": provenance_map[cid]["original_scores"],
            }
            results.append(c)

        logger.debug(
            f"RRF Fusion merged {len(ranked_lists)} lists ({sum(len(l) for l in ranked_lists)} raw chunks) "
            f"into {len(results)} unified chunks (k={self.k})"
        )
        return results
