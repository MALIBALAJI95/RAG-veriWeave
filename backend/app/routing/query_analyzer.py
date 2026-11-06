"""Query analyzer extracting structural, lexical, and intent signals."""

import re
from typing import Dict, List, Set
from pydantic import BaseModel, Field


class QuerySignals(BaseModel):
    """Signals extracted from query text."""
    raw_query: str
    cleaned_query: str
    token_count: int
    has_sql_keywords: bool = False
    sql_intent_score: float = 0.0
    has_web_keywords: bool = False
    web_intent_score: float = 0.0
    has_multi_source_indicators: bool = False
    has_exact_identifiers: bool = False
    target_file_type: str | None = None
    target_page: int | None = None
    detected_keywords: List[str] = Field(default_factory=list)


# Keywords suggesting structured database catalog lookup
SQL_PATTERNS = [
    r"\b(how many|count of|number of)\s+(?:all\s+)?(?:total\s+)?(?:indexed\s+)?(documents|files|pages|chunks)\b",
    r"\b(how many|count of|number of)\s+(?:total\s+)?(pdf|docx|txt|md)\b",
    r"\b(list|show|what are)\s+(?:all\s+)?(?:the\s+)?(?:uploaded\s+)?(?:indexed\s+)?(documents|files|filenames)\b",
    r"\b(file size|file sizes|average size|largest file|biggest document)\b",
    r"\b(total pages|page count|total chunks)\b",
    r"\b(when was .* uploaded|upload date|indexing status)\b",
    r"\b(in the database|in sqlite|in the catalog|indexed in database)\b",
]

# Keywords suggesting external web search for recent or external knowledge
WEB_PATTERNS = [
    r"\b(latest|recent|current|today|breaking|news)\b",
    r"\b(what is happening in|new developments in|release date of)\b",
    r"\b(2025|2026)\b",
    r"\b(external documentation|online reference|web benchmark)\b",
]

# Indicators of compound questions requiring multi-source synthesis
MULTI_SOURCE_PATTERNS = [
    r"\b(compare|contrast)\s+.*(?:internal|uploaded|our document|our internal).*with.*(?:external|web|online|latest)\b",
    r"\b(?:internal|uploaded|our document).*and.*(?:latest|external|web|online|news)\b",
    r"\b(?:external|web|online).*and.*(?:internal|uploaded|document|catalog)\b",
    r"\band\s+(?:check\s+)?(?:how many|what is the file size|check the database|look up the upload date)\b",
    r"\b(?:compared to current|versus the latest online|and compare with today)\b",
    r"\b(?:in our document .* and also (?:find|search|check))\b",
]


class QueryAnalyzer:
    """Analyzes questions to extract routing indicators."""

    def analyze(self, query: str) -> QuerySignals:
        cleaned = query.strip()
        q_lower = cleaned.lower()
        tokens = cleaned.split()

        # SQL Signals
        sql_hits = 0
        for pat in SQL_PATTERNS:
            if re.search(pat, q_lower):
                sql_hits += 1
        has_sql = sql_hits > 0
        sql_score = min(1.0, sql_hits * 0.45)

        # Web Signals
        web_hits = 0
        for pat in WEB_PATTERNS:
            if re.search(pat, q_lower):
                web_hits += 1
        has_web = web_hits > 0
        web_score = min(1.0, web_hits * 0.45)

        # Multi-Source Indicators
        has_multi = False
        for pat in MULTI_SOURCE_PATTERNS:
            if re.search(pat, q_lower):
                has_multi = True
                break

        # Also multi-source if both strong SQL and strong vector document questions exist
        if has_sql and (has_web or (any(k in q_lower for k in ["explain", "summarize", "what is", "method", "content", "architecture"]) and any(c in q_lower for c in ["and", "also", "plus"]))):
            has_multi = True

        # Exact identifiers (e.g. filename with extension, acronyms or quotes)
        has_exact = bool(re.search(r'["\'].+?["\']|\b[a-zA-Z0-9_\-]+\.(?:pdf|docx|txt|md)\b|\b(bm25|hnsw|rrf|cosine|tf-idf)\b', q_lower))

        # Extracted file type / page
        ft_match = re.search(r"\b(pdf|docx|txt|md)\b", q_lower)
        target_ft = ft_match.group(1) if ft_match else None

        page_match = re.search(r"\bpage\s+(\d+)\b", q_lower)
        target_page = int(page_match.group(1)) if page_match else None

        return QuerySignals(
            raw_query=query,
            cleaned_query=cleaned,
            token_count=len(tokens),
            has_sql_keywords=has_sql,
            sql_intent_score=sql_score,
            has_web_keywords=has_web,
            web_intent_score=web_score,
            has_multi_source_indicators=has_multi,
            has_exact_identifiers=has_exact,
            target_file_type=target_ft,
            target_page=target_page,
        )
