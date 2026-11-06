"""Retrieval strategy enumeration for VeriWeave."""

from enum import Enum


class RetrievalStrategy(str, Enum):
    """Supported retrieval strategies in VeriWeave."""
    BASELINE = "baseline"               # Dense similarity search (Phase 1)
    MULTI_QUERY = "multi_query"         # LLM-generated semantic query variants
    HYDE = "hyde"                       # Hypothetical Document Embeddings
    DECOMPOSITION = "decomposition"     # Sub-query decomposition for compound queries
    FUSION = "fusion"                   # Multi-strategy Reciprocal Rank Fusion
    HYBRID = "hybrid"                   # Dense (SentenceTransformers) + Sparse (BM25)
    HYBRID_RERANK = "hybrid_rerank"     # Hybrid retrieval + Cross-Encoder reranking
    RERANK = "rerank"                   # Baseline dense retrieval + Cross-Encoder reranking
