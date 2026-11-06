"""Central routing orchestrator coordinating classification, handler execution, and multi-source synthesis."""

import time
from typing import Any, Dict, List, Optional, Tuple
from backend.app.core.logging import get_logger
from backend.app.routing.classifier import RouteClassifier
from backend.app.routing.evidence import EvidenceItem
from backend.app.routing.handlers.sql_handler import SQLRouteHandler
from backend.app.routing.handlers.vector_handler import VectorRouteHandler
from backend.app.routing.handlers.web_handler import WebRouteHandler
from backend.app.routing.schemas import RouteCategory, RoutingDecision, RoutingMode
from backend.app.schemas.chat import MetadataFilter
from backend.app.schemas.strategy import RetrievalStrategy

logger = get_logger(__name__)


class RoutingOrchestrator:
    """Classifies queries and orchestrates execution across vector, SQL, web, and multi-source paths."""

    def __init__(
        self,
        classifier: RouteClassifier,
        vector_handler: VectorRouteHandler,
        sql_handler: SQLRouteHandler,
        web_handler: WebRouteHandler,
    ):
        self.classifier = classifier
        self.vector_handler = vector_handler
        self.sql_handler = sql_handler
        self.web_handler = web_handler

    def route_and_retrieve(
        self,
        query: str,
        routing_mode: RoutingMode = RoutingMode.AUTO,
        selected_strategy: Optional[RetrievalStrategy] = None,
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        rerank: bool = False,
        filters: Optional[MetadataFilter] = None,
        doc_id_filter: Optional[str] = None,
    ) -> Tuple[List[EvidenceItem], RoutingDecision, Dict[str, Any]]:
        """Determine optimal route, execute handlers, and synthesize unified cross-source evidence."""
        start_time = time.perf_counter()

        # 1. Classify query intent
        decision = self.classifier.classify(
            query=query,
            routing_mode=routing_mode,
            selected_strategy=selected_strategy,
        )

        evidence: List[EvidenceItem] = []
        sources_queried: List[str] = []
        failed_sources: List[str] = []

        logger.info(
            f"Routing decision: route={decision.route.value}, confidence={decision.confidence:.2f}, "
            f"method={decision.classification_method}"
        )

        # 2. Dispatch to route handlers
        if decision.route == RouteCategory.VECTOR_DOCUMENT:
            sources_queried.append("vector_document")
            evidence = self.vector_handler.execute(
                query=query,
                strategy=decision.selected_strategy or RetrievalStrategy.BASELINE,
                top_k=top_k,
                score_threshold=score_threshold,
                rerank=rerank,
                filters=filters,
                doc_id_filter=doc_id_filter,
            )

        elif decision.route == RouteCategory.STRUCTURED_SQL:
            sources_queried.append("structured_sql")
            evidence = self.sql_handler.execute(query=query)

        elif decision.route == RouteCategory.WEB_SEARCH:
            sources_queried.append("web_search")
            evidence = self.web_handler.execute(query=query)

        elif decision.route == RouteCategory.MULTI_SOURCE:
            # Multi-source concurrent / sequential synthesis
            # 1. Vector Document Retrieval
            try:
                sources_queried.append("vector_document")
                vec_query = decision.sub_queries.get("vector_document", query)
                vec_items = self.vector_handler.execute(
                    query=vec_query,
                    strategy=decision.selected_strategy or RetrievalStrategy.HYBRID,
                    top_k=max(2, top_k // 2),
                    score_threshold=score_threshold,
                    rerank=rerank,
                    filters=filters,
                    doc_id_filter=doc_id_filter,
                )
                evidence.extend(vec_items)
            except Exception as e:
                logger.error(f"Multi-source vector retrieval failed: {e}")
                failed_sources.append(f"vector_document: {str(e)}")

            # 2. Structured SQL Retrieval
            try:
                sources_queried.append("structured_sql")
                sql_query = decision.sub_queries.get("structured_sql", query)
                sql_items = self.sql_handler.execute(query=sql_query)
                evidence.extend(sql_items)
            except Exception as e:
                logger.error(f"Multi-source SQL retrieval failed: {e}")
                failed_sources.append(f"structured_sql: {str(e)}")

            # 3. Web Search Retrieval
            try:
                sources_queried.append("web_search")
                web_query = decision.sub_queries.get("web_search", query)
                web_items = self.web_handler.execute(query=web_query)
                evidence.extend(web_items)
            except Exception as e:
                logger.error(f"Multi-source web search failed: {e}")
                failed_sources.append(f"web_search: {str(e)}")

            # Deduplicate evidence by source_id
            seen_source_ids = set()
            deduped_evidence = []
            for item in evidence:
                if item.source_id not in seen_source_ids:
                    seen_source_ids.add(item.source_id)
                    deduped_evidence.append(item)
            evidence = deduped_evidence[: max(top_k * 2, 6)]

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        execution_meta = {
            "route_selected": decision.route.value,
            "confidence": decision.confidence,
            "classification_method": decision.classification_method,
            "sources_queried": sources_queried,
            "failed_sources": failed_sources,
            "evidence_item_count": len(evidence),
            "routing_latency_ms": round(elapsed_ms, 2),
        }

        logger.info(
            f"RoutingOrchestrator completed in {elapsed_ms:.2f}ms: "
            f"{len(evidence)} items from {sources_queried}"
        )
        return evidence, decision, execution_meta
