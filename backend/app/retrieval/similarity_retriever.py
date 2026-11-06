"""Baseline semantic similarity retriever using dense embeddings and Qdrant."""

from typing import List, Optional
from backend.app.core.exceptions import VectorStorageError
from backend.app.core.logging import get_logger
from backend.app.embeddings.base import BaseEmbeddings
from backend.app.retrieval.base import BaseRetriever
from backend.app.schemas.chat import MetadataFilter, RetrievedChunk
from backend.app.storage.qdrant_client import QdrantStorageManager

logger = get_logger(__name__)


class SimilarityRetriever(BaseRetriever):
    """Retrieves document chunks using dense cosine similarity in Qdrant."""

    def __init__(
        self,
        storage_manager: QdrantStorageManager,
        embedding_model: BaseEmbeddings,
        collection_name: str = "veriweave_documents",
    ):
        self.storage = storage_manager
        self.embeddings = embedding_model
        self.collection_name = collection_name

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        doc_id_filter: Optional[str] = None,
        filters: Optional[MetadataFilter] = None,
    ) -> List[RetrievedChunk]:
        """Encode query into dense vector and search Qdrant for top matching chunks."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        # Merge legacy doc_id_filter and rich MetadataFilter
        effective_doc_id = (filters.doc_id if filters else None) or doc_id_filter
        filename_filter = filters.filename if filters else None
        page_number_filter = filters.page_number if filters else None
        custom_filter = filters.custom if filters else None

        logger.debug(f"Executing similarity retrieval for: '{cleaned_query[:60]}...' (top_k={top_k})")
        query_vector = self.embeddings.embed_query(cleaned_query)

        results = self.storage.search_similar(
            collection_name=self.collection_name,
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=score_threshold,
            doc_id_filter=effective_doc_id,
            filename_filter=filename_filter,
            page_number_filter=page_number_filter,
            custom_filter=custom_filter,
        )

        for rank, chunk in enumerate(results, 1):
            chunk.original_rank = rank
            chunk.retrieval_method = "dense"

        return results
