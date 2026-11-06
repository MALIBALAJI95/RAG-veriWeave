"""Execution handler for structured SQL catalog retrieval."""

from typing import List, Optional
from backend.app.core.logging import get_logger
from backend.app.database.nl_to_sql import NLToSQLTranslator
from backend.app.database.sql_validator import SafeSQLExecutor
from backend.app.generation.ollama_client import OllamaClient
from backend.app.routing.evidence import EvidenceItem, from_sql_result

logger = get_logger(__name__)


class SQLRouteHandler:
    """Handles structured catalog questions with natural-language-to-SQL translation and safe execution."""

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        max_rows: int = 50,
        timeout_seconds: float = 5.0,
    ):
        self.executor = SafeSQLExecutor(max_rows=max_rows, timeout_seconds=timeout_seconds)
        self.translator = NLToSQLTranslator(ollama_client=ollama_client, executor=self.executor)

    def execute(self, query: str) -> List[EvidenceItem]:
        """Translate question to SQL, execute safely with allowlists, and return normalized EvidenceItems."""
        sql_query, method = self.translator.translate_to_sql(query)
        logger.info(f"SQLRouteHandler translated '{query[:50]}' -> '{sql_query}' (via {method})")

        res = self.executor.execute(sql_query)

        if not res["success"]:
            logger.warning(f"SQL Execution rejected or failed: {res.get('error')}")
            return [
                EvidenceItem(
                    evidence_id="ev_sql_err",
                    source_type="structured_sql",
                    source_id=sql_query,
                    content_excerpt=f"Structured catalog query could not be executed: {res.get('error')}",
                    score=0.0,
                    metadata={"sql_query": sql_query, "error": res.get("error"), "rejected": True},
                )
            ]

        evidence_items = from_sql_result(
            query_executed=res["query_executed"],
            rows=res["rows"],
            latency_ms=res["latency_ms"],
        )
        logger.info(f"SQLRouteHandler produced {len(evidence_items)} evidence items in {res['latency_ms']:.2f}ms")
        return evidence_items
