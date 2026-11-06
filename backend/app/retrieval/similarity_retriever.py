"""Baseline semantic similarity retriever using dense embeddings and Qdrant."""

from typing import List, Optional
from backend.app.core.exceptions import VectorStorageError
from backend.app.core.logging import get_logger
from backend.app.embeddings.base import BaseEmbeddings
from backend.app.retrieval.base import BaseRetriever
from backend.app.schemas.chat import RetrievedChunk
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
    ) -> List[RetrievedChunk]:
        """Encode query into dense vector and search Qdrant for top matching chunks."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        logger.debug(f"Executing similarity retrieval for: '{cleaned_query[:60]}...' (top_k={top_k})")
        query_vector = self.embeddings.embed_query(cleaned_query)

        results = self.storage.search_similar(
            collection_name=self.collection_name,
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=score_threshold,
            doc_id_filter=doc_id_filter,
        )
        return results
