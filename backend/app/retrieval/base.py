"""Base retriever abstraction with rich metadata filtering."""

from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.schemas.chat import MetadataFilter, RetrievedChunk


class BaseRetriever(ABC):
    """Abstract interface for all document retrieval strategies."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        doc_id_filter: Optional[str] = None,
        filters: Optional[MetadataFilter] = None,
    ) -> List[RetrievedChunk]:
        """Retrieve most relevant chunks for the given query."""
        pass
