"""Execution handler for external web search queries."""

from typing import List, Optional
from backend.app.core.logging import get_logger
from backend.app.routing.evidence import EvidenceItem, from_search_result
from backend.app.web_search.base import BaseWebSearchProvider
from backend.app.web_search.factory import get_web_search_provider

logger = get_logger(__name__)


class WebRouteHandler:
    """Handles external queries via configured search provider."""

    def __init__(self, provider: Optional[BaseWebSearchProvider] = None, max_results: int = 3):
        self.provider = provider or get_web_search_provider()
        self.max_results = max_results

    def execute(self, query: str) -> List[EvidenceItem]:
        """Query search provider and normalize results into unified EvidenceItems."""
        if not self.provider.is_available:
            logger.info("External web search route requested but provider is disabled or unavailable.")
            return [
                EvidenceItem(
                    evidence_id="ev_web_disabled",
                    source_type="web_search",
                    source_id="web_search_disabled",
                    title="External Search Unavailable",
                    content_excerpt="External web search is currently disabled or no provider is configured.",
                    score=0.0,
                    metadata={"provider": self.provider.provider_name, "unavailable": True},
                )
            ]

        try:
            results = self.provider.search(query=query, max_results=self.max_results)
            evidence_items = [from_search_result(r, idx) for idx, r in enumerate(results, 1)]
            logger.info(f"WebRouteHandler retrieved {len(evidence_items)} external items via {self.provider.provider_name}")
            return evidence_items
        except Exception as e:
            logger.error(f"WebRouteHandler error: {e}")
            return [
                EvidenceItem(
                    evidence_id="ev_web_err",
                    source_type="web_search",
                    source_id="web_search_failed",
                    title="External Search Error",
                    content_excerpt=f"External search attempt encountered an error: {str(e)}",
                    score=0.0,
                    metadata={"error": str(e), "failed": True},
                )
            ]
