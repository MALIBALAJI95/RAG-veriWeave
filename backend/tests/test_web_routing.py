"""Tests for web search provider abstraction, mock provider, and web route handler."""

import pytest
from backend.app.routing.evidence import EvidenceItem
from backend.app.routing.handlers.web_handler import WebRouteHandler
from backend.app.web_search.base import SearchResult
from backend.app.web_search.mock_provider import MockWebSearchProvider


def test_mock_web_search_provider_known_query():
    """MockWebSearchProvider must return realistic topic-relevant search results."""
    provider = MockWebSearchProvider(enabled=True)
    results = provider.search("What are the latest LangGraph agent features?", max_results=3)

    assert len(results) >= 1
    first = results[0]
    assert isinstance(first, SearchResult)
    assert "langgraph" in first.title.lower() or "langchain" in first.title.lower()
    assert first.url.startswith("http")
    assert len(first.snippet) > 20
    assert first.metadata["provider"] == "mock_web_search"
    assert first.score > 0.0


def test_mock_web_search_provider_fallback_query():
    """MockWebSearchProvider must return generic search results for queries not in reference dictionary."""
    provider = MockWebSearchProvider(enabled=True)
    results = provider.search("quantum teleportation protocols in 2026", max_results=2)

    assert len(results) >= 1
    assert "quantum teleportation" in results[0].snippet.lower() or "quantum teleportation" in results[0].title.lower()


def test_web_route_handler_normalizes_to_evidence():
    """WebRouteHandler must translate SearchResults into unified EvidenceItems."""
    provider = MockWebSearchProvider(enabled=True)
    handler = WebRouteHandler(provider=provider, max_results=2)

    evidence_items = handler.execute("qdrant vector database hybrid search")
    assert len(evidence_items) >= 1
    for item in evidence_items:
        assert isinstance(item, EvidenceItem)
        assert item.source_type == "web_search"
        assert item.url is not None
        assert item.title is not None
        assert len(item.content_excerpt) > 10

        # Verify citation conversion preserves web origin
        citation = item.to_citation(citation_id=1)
        assert "Web:" in citation.filename
        assert "[Web URL:" in citation.snippet


def test_web_route_handler_handles_disabled_provider():
    """WebRouteHandler must gracefully handle disabled provider and return placeholder evidence."""
    provider = MockWebSearchProvider(enabled=False)
    handler = WebRouteHandler(provider=provider, max_results=5)

    evidence_items = handler.execute("test query")
    assert len(evidence_items) == 1
    assert evidence_items[0].evidence_id == "ev_web_disabled"
    assert "disabled" in evidence_items[0].content_excerpt.lower()
