"""Web search provider factory."""

from backend.app.core.config import get_settings
from backend.app.web_search.base import BaseWebSearchProvider
from backend.app.web_search.duckduckgo_provider import DuckDuckGoSearchProvider
from backend.app.web_search.mock_provider import MockWebSearchProvider


def get_web_search_provider() -> BaseWebSearchProvider:
    """Instantiate configured search provider based on environment settings."""
    settings = get_settings()
    provider_type = settings.WEB_SEARCH_PROVIDER.lower().strip()
    enabled = settings.ENABLE_WEB_SEARCH

    if not enabled or provider_type == "none":
        return MockWebSearchProvider(enabled=False)
    elif provider_type == "duckduckgo":
        return DuckDuckGoSearchProvider(enabled=True)
    else:
        return MockWebSearchProvider(enabled=True)
