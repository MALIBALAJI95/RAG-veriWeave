"""Lexical sparse retrieval engine using BM25 Okapi."""

import re
from typing import Dict, List, Optional
from rank_bm25 import BM25Okapi
from backend.app.core.logging import get_logger
from backend.app.retrieval.base import BaseRetriever
from backend.app.schemas.chat import MetadataFilter, RetrievedChunk
from backend.app.schemas.document import DocumentChunk
from backend.app.storage.qdrant_client import QdrantStorageManager

logger = get_logger(__name__)


def tokenize_text(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return re.findall(r"\w+", text.lower())


class BM25Retriever(BaseRetriever):
    """Lexical sparse retriever using BM25 over indexed Qdrant chunks."""

    def __init__(
        self,
        storage_manager: QdrantStorageManager,
        collection_name: str = "veriweave_documents",
    ):
        self.storage = storage_manager
        self.collection_name = collection_name
        self.bm25: Optional[BM25Okapi] = None
        self.chunks_cache: List[DocumentChunk] = []
        self._is_indexed: bool = False

    def build_index(self, force_rebuild: bool = False) -> int:
        """Fetch all chunks from storage and construct in-memory BM25 index."""
        if self._is_indexed and not force_rebuild:
            return len(self.chunks_cache)

        chunks = self.storage.get_all_chunks(self.collection_name)
        if not chunks:
            self.chunks_cache = []
            self.bm25 = None
            self._is_indexed = True
            logger.debug(f"BM25 index built: 0 chunks in '{self.collection_name}'")
            return 0

        corpus_tokens = [tokenize_text(c.text) for c in chunks]
        self.bm25 = BM25Okapi(corpus_tokens)
        self.chunks_cache = chunks
        self._is_indexed = True
        logger.info(f"Built BM25 index over {len(chunks)} chunks in collection '{self.collection_name}'")
        return len(chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        doc_id_filter: Optional[str] = None,
        filters: Optional[MetadataFilter] = None,
    ) -> List[RetrievedChunk]:
        """Perform BM25 lexical search with optional metadata filtering."""
        query_tokens = tokenize_text(query)
        if not query_tokens:
            return []

        # Ensure index exists
        self.build_index()
        if not self.bm25 or not self.chunks_cache:
            return []

        # Raw BM25 scores
        raw_scores = self.bm25.get_scores(query_tokens)

        # Normalization: map raw scores to relative 0.0 - 1.0 range
        max_score = float(max(raw_scores)) if len(raw_scores) > 0 else 1.0
        norm_factor = max_score if max_score > 0 else 1.0

        effective_doc_id = (filters.doc_id if filters else None) or doc_id_filter
        filename_filter = filters.filename if filters else None
        page_filter = filters.page_number if filters else None

        candidates = []
        for idx, score in enumerate(raw_scores):
            if score <= 0.0:
                continue

            chunk = self.chunks_cache[idx]

            # Apply metadata filters
            if effective_doc_id and chunk.doc_id != effective_doc_id:
                continue
            if filename_filter and chunk.filename != filename_filter:
                continue
            if page_filter is not None and chunk.page_number != page_filter:
                continue
            if filters and filters.custom:
                m = chunk.metadata or {}
                if not all(m.get(k) == v for k, v in filters.custom.items()):
                    continue

            norm_score = round(float(score) / norm_factor, 4)
            if score_threshold is not None and norm_score < score_threshold:
                continue

            candidates.append((norm_score, score, chunk))

        # Sort descending by score
        candidates.sort(key=lambda x: x[0], reverse=True)

        results: List[RetrievedChunk] = []
        for rank, (norm_score, raw_score, c) in enumerate(candidates[:top_k], 1):
            results.append(
                RetrievedChunk(
                    chunk_id=c.chunk_id,
                    doc_id=c.doc_id,
                    filename=c.filename,
                    page_number=c.page_number,
                    chunk_index=c.chunk_index,
                    text=c.text,
                    score=norm_score,
                    original_rank=rank,
                    retrieval_method="bm25_sparse",
                    metadata={
                        **c.metadata,
                        "raw_bm25_score": round(float(raw_score), 4),
                    },
                )
            )

        logger.debug(f"BM25 retrieved {len(results)} chunks for query: '{query[:50]}...'")
        return results
