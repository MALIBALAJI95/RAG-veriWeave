"""Web search module exports."""

from backend.app.web_search.base import BaseWebSearchProvider, SearchResult
from backend.app.web_search.duckduckgo_provider import DuckDuckGoSearchProvider
from backend.app.web_search.factory import get_web_search_provider
from backend.app.web_search.mock_provider import MockWebSearchProvider

__all__ = [
    "BaseWebSearchProvider",
    "SearchResult",
    "MockWebSearchProvider",
    "DuckDuckGoSearchProvider",
    "get_web_search_provider",
]
