"""Hybrid dense + sparse retriever combining Sentence-Transformers with BM25 via RRF."""

from typing import List, Optional
from backend.app.core.logging import get_logger
from backend.app.retrieval.base import BaseRetriever
from backend.app.retrieval.bm25 import BM25Retriever
from backend.app.retrieval.fusion import RRFFusionEngine
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.schemas.chat import MetadataFilter, RetrievedChunk

logger = get_logger(__name__)


class HybridRetriever(BaseRetriever):
    """Combines dense semantic vector retrieval (Qdrant) and sparse lexical retrieval (BM25)."""

    def __init__(
        self,
        dense_retriever: SimilarityRetriever,
        sparse_retriever: BM25Retriever,
        rrf_k: int = 60,
    ):
        self.dense = dense_retriever
        self.sparse = sparse_retriever
        self.fusion_engine = RRFFusionEngine(k=rrf_k)

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        doc_id_filter: Optional[str] = None,
        filters: Optional[MetadataFilter] = None,
    ) -> List[RetrievedChunk]:
        """Perform concurrent or sequential dense and sparse search, then fuse via RRF."""
        # Retrieve extra candidate depth for fusion (e.g. 2x top_k)
        candidate_depth = max(top_k * 2, 8)

        # 1. Dense search
        dense_results = self.dense.retrieve(
            query=query,
            top_k=candidate_depth,
            score_threshold=score_threshold,
            doc_id_filter=doc_id_filter,
            filters=filters,
        )

        # 2. Sparse search
        sparse_results = self.sparse.retrieve(
            query=query,
            top_k=candidate_depth,
            score_threshold=score_threshold,
            doc_id_filter=doc_id_filter,
            filters=filters,
        )

        # If one channel is empty, return the other directly
        if not dense_results and not sparse_results:
            return []
        if not dense_results:
            return sparse_results[:top_k]
        if not sparse_results:
            return dense_results[:top_k]

        # 3. Fuse using Reciprocal Rank Fusion
        fused = self.fusion_engine.fuse(
            ranked_lists=[dense_results, sparse_results],
            top_k=top_k,
            source_labels=["dense_semantic", "bm25_lexical"],
        )

        for chunk in fused:
            chunk.retrieval_method = "hybrid_dense_bm25"

        logger.info(
            f"Hybrid retrieval merged {len(dense_results)} dense and {len(sparse_results)} sparse candidates "
            f"into top {len(fused)} chunks"
        )
        return fused
