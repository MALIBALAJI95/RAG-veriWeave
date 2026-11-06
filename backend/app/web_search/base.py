"""Base interface and schemas for web search providers."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Normalized external web search result item."""
    title: str = Field(description="Page or article title")
    url: str = Field(description="Source URL")
    snippet: str = Field(description="Relevant text excerpt or summary")
    score: float = Field(default=0.8, description="Relevance score (0.0 to 1.0)")
    published_date: Optional[str] = Field(default=None, description="Publication date if available")
    retrieval_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseWebSearchProvider(ABC):
    """Abstract interface for external search providers."""

    @abstractmethod
    def search(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """Execute web search and return structured results."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the provider is configured and operational."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the search provider."""
        pass
