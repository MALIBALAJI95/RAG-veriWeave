"""Deterministic mock web search provider for reproducible benchmarks and testing."""

from datetime import datetime
from typing import List
from backend.app.core.logging import get_logger
from backend.app.web_search.base import BaseWebSearchProvider, SearchResult

logger = get_logger(__name__)

# Curated reference database for deterministic mock search
MOCK_KNOWLEDGE_BASE = [
    {
        "keywords": ["langgraph", "agent", "workflow", "state"],
        "title": "LangGraph: Cyclical Multi-Agent StateGraph Architecture",
        "url": "https://python.langchain.com/docs/langgraph/concepts",
        "snippet": (
            "LangGraph enables building cyclical multi-agent workflows with fine-grained state management, "
            "human-in-the-loop validation, checkpointing, and dynamic tool orchestration."
        ),
    },
    {
        "keywords": ["qdrant", "vector", "hybrid", "hnsw"],
        "title": "Qdrant Vector Database Official Documentation - Architecture",
        "url": "https://qdrant.tech/documentation/concepts",
        "snippet": (
            "Qdrant implements Hierarchical Navigable Small World (HNSW) vector graphs with payload filtering, "
            "on-disk vector quantization, sparse vector support, and high-concurrency search."
        ),
    },
    {
        "keywords": ["rag", "fusion", "reciprocal rank", "rrf"],
        "title": "Reciprocal Rank Fusion in Modern Information Retrieval",
        "url": "https://dl.acm.org/doi/10.1145/1571941.1572114",
        "snippet": (
            "Reciprocal Rank Fusion (RRF) scores documents inversely proportional to their rank position across "
            "multiple diverse retrieval engines without requiring calibrated score normalization."
        ),
    },
    {
        "keywords": ["python", "release", "python 3.12", "performance"],
        "title": "Python 3.12 Release Highlights and Feature Summary",
        "url": "https://docs.python.org/3.12/whatsnew/3.12.html",
        "snippet": (
            "Python 3.12 delivers improved error messages, isolated subinterpreters, comprehension inlining, "
            "and reduced memory footprint for optimized execution on modern operating systems."
        ),
    },
]


class MockWebSearchProvider(BaseWebSearchProvider):
    """Deterministic web search provider for offline execution and testing."""

    def __init__(self, enabled: bool = True):
        self._enabled = enabled

    @property
    def is_available(self) -> bool:
        return self._enabled

    @property
    def provider_name(self) -> str:
        return "mock_web_search"

    def search(self, query: str, max_results: int = 3) -> List[SearchResult]:
        if not self._enabled:
            return []

        q_terms = set(query.lower().split())
        scored_matches = []

        for entry in MOCK_KNOWLEDGE_BASE:
            match_count = sum(1 for kw in entry["keywords"] if kw in query.lower() or kw in q_terms)
            if match_count > 0:
                score = min(0.95, 0.6 + match_count * 0.1)
                scored_matches.append((score, entry))

        # Sort descending by match score
        scored_matches.sort(key=lambda x: x[0], reverse=True)

        results: List[SearchResult] = []
        now_ts = datetime.utcnow().isoformat()

        for score, entry in scored_matches[:max_results]:
            results.append(
                SearchResult(
                    title=entry["title"],
                    url=entry["url"],
                    snippet=entry["snippet"],
                    score=round(score, 4),
                    retrieval_timestamp=now_ts,
                    metadata={"provider": self.provider_name},
                )
            )

        # Fallback general match if no keyword hit
        if not results:
            results.append(
                SearchResult(
                    title=f"External Technical Information regarding: {query[:40]}",
                    url="https://en.wikipedia.org/wiki/Information_retrieval",
                    snippet=f"General reference overview discussing concepts and standards related to {query}.",
                    score=0.65,
                    retrieval_timestamp=now_ts,
                    metadata={"provider": self.provider_name, "general_fallback": True},
                )
            )

        logger.info(f"MockWebSearch retrieved {len(results)} external results for: '{query[:40]}...'")
        return results[:max_results]
