"""Base embedding model abstraction."""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddings(ABC):
    """Abstract interface for dense embedding models."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings for a list of document strings."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate dense vector embedding for a query string."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimensionality of the embedding model."""
        pass
