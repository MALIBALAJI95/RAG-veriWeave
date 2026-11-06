"""Central retrieval orchestrator supporting multi-strategy selection, fusion, and reranking."""

import time
from typing import List, Optional, Tuple
from backend.app.core.logging import get_logger
from backend.app.retrieval.base import BaseRetriever
from backend.app.retrieval.bm25 import BM25Retriever
from backend.app.retrieval.decomposition import QueryDecompositionRetriever
from backend.app.retrieval.fusion import RRFFusionEngine
from backend.app.retrieval.hybrid import HybridRetriever
from backend.app.retrieval.hyde import HyDERetriever
from backend.app.retrieval.multi_query import MultiQueryRetriever
from backend.app.retrieval.reranker import CrossEncoderReranker
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.schemas.chat import MetadataFilter, RetrievalMetadata, RetrievalStrategy, RetrievedChunk

logger = get_logger(__name__)


class RetrievalOrchestrator:
    """Orchestrates query execution across baseline, multi-query, HyDE, decomposition, hybrid, and reranking."""

    def __init__(
        self,
        baseline_retriever: SimilarityRetriever,
        multi_query_retriever: MultiQueryRetriever,
        hyde_retriever: HyDERetriever,
        decomposition_retriever: QueryDecompositionRetriever,
        sparse_retriever: BM25Retriever,
        hybrid_retriever: HybridRetriever,
        reranker: CrossEncoderReranker,
        fusion_engine: RRFFusionEngine,
    ):
        self.baseline = baseline_retriever
        self.multi_query = multi_query_retriever
        self.hyde = hyde_retriever
        self.decomposition = decomposition_retriever
        self.sparse = sparse_retriever
        self.hybrid = hybrid_retriever
        self.reranker = reranker
        self.fusion = fusion_engine

    def retrieve(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.BASELINE,
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        rerank: bool = False,
        doc_id_filter: Optional[str] = None,
        filters: Optional[MetadataFilter] = None,
    ) -> Tuple[List[RetrievedChunk], RetrievalMetadata]:
        """Execute selected retrieval strategy, optionally rerank, and build structured diagnostics."""
        start_time = time.perf_counter()
        cleaned_query = query.strip()
        if not cleaned_query:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return [], RetrievalMetadata(
                strategy=strategy,
                retrieval_latency_ms=round(elapsed_ms, 2),
            )

        # Candidate depth when reranking is scheduled
        needs_rerank = rerank or strategy in (RetrievalStrategy.HYBRID_RERANK, RetrievalStrategy.RERANK)
        initial_top_k = max(top_k * 2, 10) if needs_rerank else top_k

        generated_queries: List[str] = []
        hypothetical_doc: Optional[str] = None
        sub_queries: List[str] = []
        fusion_applied: bool = False

        # Route by strategy
        if strategy == RetrievalStrategy.BASELINE:
            candidates = self.baseline.retrieve(
                query=cleaned_query,
                top_k=initial_top_k,
                score_threshold=score_threshold,
                doc_id_filter=doc_id_filter,
                filters=filters,
            )

        elif strategy == RetrievalStrategy.MULTI_QUERY:
            candidates = self.multi_query.retrieve(
                query=cleaned_query,
                top_k=initial_top_k,
                score_threshold=score_threshold,
                doc_id_filter=doc_id_filter,
                filters=filters,
            )
            generated_queries = list(self.multi_query.last_generated_queries)
            fusion_applied = True

        elif strategy == RetrievalStrategy.HYDE:
            candidates = self.hyde.retrieve(
                query=cleaned_query,
                top_k=initial_top_k,
                score_threshold=score_threshold,
                doc_id_filter=doc_id_filter,
                filters=filters,
            )
            hypothetical_doc = self.hyde.last_hypothetical_document

        elif strategy == RetrievalStrategy.DECOMPOSITION:
            candidates = self.decomposition.retrieve(
                query=cleaned_query,
                top_k=initial_top_k,
                score_threshold=score_threshold,
                doc_id_filter=doc_id_filter,
                filters=filters,
            )
            sub_queries = list(self.decomposition.last_subqueries)
            fusion_applied = True

        elif strategy == RetrievalStrategy.FUSION:
            # Multi-perspective fusion: dense + sparse + hyde
            dense_cand = self.baseline.retrieve(
                query=cleaned_query,
                top_k=initial_top_k,
                score_threshold=score_threshold,
                doc_id_filter=doc_id_filter,
                filters=filters,
            )
            sparse_cand = self.sparse.retrieve(
                query=cleaned_query,
                top_k=initial_top_k,
                score_threshold=score_threshold,
                doc_id_filter=doc_id_filter,
                filters=filters,
            )
            candidates = self.fusion.fuse(
                ranked_lists=[dense_cand, sparse_cand],
                top_k=initial_top_k,
                source_labels=["dense", "bm25"],
            )
            fusion_applied = True

        elif strategy in (RetrievalStrategy.HYBRID, RetrievalStrategy.HYBRID_RERANK):
            candidates = self.hybrid.retrieve(
                query=cleaned_query,
                top_k=initial_top_k,
                score_threshold=score_threshold,
                doc_id_filter=doc_id_filter,
                filters=filters,
            )
            fusion_applied = True

        elif strategy == RetrievalStrategy.RERANK:
            candidates = self.baseline.retrieve(
                query=cleaned_query,
                top_k=initial_top_k,
                score_threshold=score_threshold,
                doc_id_filter=doc_id_filter,
                filters=filters,
            )
        else:
            logger.warning(f"Unknown strategy '{strategy}'. Defaulting to baseline similarity.")
            candidates = self.baseline.retrieve(
                query=cleaned_query,
                top_k=initial_top_k,
                score_threshold=score_threshold,
                doc_id_filter=doc_id_filter,
                filters=filters,
            )

        raw_candidate_count = len(candidates)

        # Apply Cross-Encoder Reranking if requested
        reranking_applied = False
        if needs_rerank and candidates:
            final_chunks = self.reranker.rerank(
                query=cleaned_query,
                chunks=candidates,
                top_k=top_k,
            )
            reranking_applied = True
        else:
            final_chunks = candidates[:top_k]

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        metadata = RetrievalMetadata(
            strategy=strategy,
            generated_queries=generated_queries,
            hypothetical_document=hypothetical_doc,
            sub_queries=sub_queries,
            fusion_applied=fusion_applied,
            reranking_applied=reranking_applied,
            raw_candidate_count=raw_candidate_count,
            returned_candidate_count=len(final_chunks),
            retrieval_latency_ms=round(elapsed_ms, 2),
        )

        logger.info(
            f"Orchestrator: strategy={strategy.value}, raw_candidates={raw_candidate_count}, "
            f"final={len(final_chunks)}, reranked={reranking_applied}, latency={elapsed_ms:.1f}ms"
        )
        return final_chunks, metadata
