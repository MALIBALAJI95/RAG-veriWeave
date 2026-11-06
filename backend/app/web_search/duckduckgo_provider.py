"""DuckDuckGo external search provider."""

from datetime import datetime
from typing import List
from backend.app.core.logging import get_logger
from backend.app.web_search.base import BaseWebSearchProvider, SearchResult

logger = get_logger(__name__)


class DuckDuckGoSearchProvider(BaseWebSearchProvider):
    """External search provider using DuckDuckGo HTML/Instant API."""

    def __init__(self, enabled: bool = True):
        self._enabled = enabled

    @property
    def is_available(self) -> bool:
        return self._enabled

    @property
    def provider_name(self) -> str:
        return "duckduckgo"

    def search(self, query: str, max_results: int = 3) -> List[SearchResult]:
        if not self._enabled:
            return []

        try:
            import httpx
            # Use DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
            with httpx.Client(timeout=4.0) as client:
                res = client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    results: List[SearchResult] = []
                    now_ts = datetime.utcnow().isoformat()

                    # Abstract
                    if data.get("AbstractText"):
                        results.append(
                            SearchResult(
                                title=data.get("Heading", query),
                                url=data.get("AbstractURL", "https://duckduckgo.com"),
                                snippet=data.get("AbstractText"),
                                score=0.88,
                                retrieval_timestamp=now_ts,
                                metadata={"provider": self.provider_name},
                            )
                        )

                    # Related topics
                    for topic in data.get("RelatedTopics", [])[: max_results - len(results)]:
                        if "Text" in topic and "FirstURL" in topic:
                            results.append(
                                SearchResult(
                                    title=topic.get("Text", "")[:60],
                                    url=topic.get("FirstURL"),
                                    snippet=topic.get("Text"),
                                    score=0.75,
                                    retrieval_timestamp=now_ts,
                                    metadata={"provider": self.provider_name},
                                )
                            )

                    if results:
                        return results[:max_results]
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed or offline ({e}).")

        return []
