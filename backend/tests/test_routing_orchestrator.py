"""Tests for RoutingOrchestrator coordination, multi-source merging, and failure tolerance."""

from unittest.mock import MagicMock
import pytest
from backend.app.routing.classifier import RouteClassifier
from backend.app.routing.evidence import EvidenceItem
from backend.app.routing.handlers.sql_handler import SQLRouteHandler
from backend.app.routing.handlers.vector_handler import VectorRouteHandler
from backend.app.routing.handlers.web_handler import WebRouteHandler
from backend.app.routing.orchestrator import RoutingOrchestrator
from backend.app.routing.schemas import RouteCategory, RoutingDecision, RoutingMode
from backend.app.schemas.chat import RetrievalStrategy


@pytest.fixture
def mock_classifier():
    classifier = MagicMock(spec=RouteClassifier)
    return classifier


@pytest.fixture
def mock_vector_handler():
    handler = MagicMock(spec=VectorRouteHandler)
    handler.execute.return_value = [
        EvidenceItem(
            evidence_id="ev_vec_1",
            source_type="vector_document",
            source_id="chunk-101",
            doc_id="doc-1",
            filename="report.pdf",
            page_number=3,
            chunk_index=2,
            content_excerpt="Vector retrieval evidence paragraph about attention mechanisms.",
            score=0.92,
        )
    ]
    return handler


@pytest.fixture
def mock_sql_handler():
    handler = MagicMock(spec=SQLRouteHandler)
    handler.execute.return_value = [
        EvidenceItem(
            evidence_id="ev_sql_1",
            source_type="structured_sql",
            source_id="SELECT COUNT(*) FROM documents",
            content_excerpt="Database record: total_documents = 42",
            score=1.0,
        )
    ]
    return handler


@pytest.fixture
def mock_web_handler():
    handler = MagicMock(spec=WebRouteHandler)
    handler.execute.return_value = [
        EvidenceItem(
            evidence_id="ev_web_1",
            source_type="web_search",
            source_id="https://example.com/latest-ai",
            title="Latest AI Models 2026",
            content_excerpt="External web information regarding latest agent developments.",
            score=0.88,
        )
    ]
    return handler


def test_orchestrator_dispatches_vector_route(mock_classifier, mock_vector_handler, mock_sql_handler, mock_web_handler):
    """RoutingOrchestrator must execute vector handler when classified as VECTOR_DOCUMENT."""
    mock_classifier.classify.return_value = RoutingDecision(
        route=RouteCategory.VECTOR_DOCUMENT,
        confidence=0.95,
        reasoning="Semantic question regarding document contents.",
        classification_method="logical_rule",
        selected_strategy=RetrievalStrategy.HYBRID,
        required_sources=["vector_document"],
    )

    orchestrator = RoutingOrchestrator(
        classifier=mock_classifier,
        vector_handler=mock_vector_handler,
        sql_handler=mock_sql_handler,
        web_handler=mock_web_handler,
    )

    evidence, decision, meta = orchestrator.route_and_retrieve(
        query="Explain the attention mechanism",
        routing_mode=RoutingMode.AUTO,
    )

    assert decision.route == RouteCategory.VECTOR_DOCUMENT
    assert len(evidence) == 1
    assert evidence[0].source_type == "vector_document"
    assert meta["route_selected"] == "vector_document"
    assert "vector_document" in meta["sources_queried"]

    mock_vector_handler.execute.assert_called_once()
    mock_sql_handler.execute.assert_not_called()
    mock_web_handler.execute.assert_not_called()


def test_orchestrator_dispatches_sql_route(mock_classifier, mock_vector_handler, mock_sql_handler, mock_web_handler):
    """RoutingOrchestrator must execute SQL handler when classified as STRUCTURED_SQL."""
    mock_classifier.classify.return_value = RoutingDecision(
        route=RouteCategory.STRUCTURED_SQL,
        confidence=0.98,
        reasoning="Count of uploaded files in database.",
        classification_method="logical_rule",
        required_sources=["structured_sql"],
    )

    orchestrator = RoutingOrchestrator(
        classifier=mock_classifier,
        vector_handler=mock_vector_handler,
        sql_handler=mock_sql_handler,
        web_handler=mock_web_handler,
    )

    evidence, decision, meta = orchestrator.route_and_retrieve(
        query="How many files are indexed?",
        routing_mode=RoutingMode.AUTO,
    )

    assert decision.route == RouteCategory.STRUCTURED_SQL
    assert len(evidence) == 1
    assert evidence[0].source_type == "structured_sql"
    mock_sql_handler.execute.assert_called_once()
    mock_vector_handler.execute.assert_not_called()


def test_orchestrator_multi_source_synthesis_and_deduplication(mock_classifier, mock_vector_handler, mock_sql_handler, mock_web_handler):
    """RoutingOrchestrator must synthesize evidence across vector, SQL, and web sources for compound queries."""
    mock_classifier.classify.return_value = RoutingDecision(
        route=RouteCategory.MULTI_SOURCE,
        confidence=0.91,
        reasoning="Compound query requiring document and web evidence.",
        classification_method="logical_rule",
        selected_strategy=RetrievalStrategy.HYBRID,
        required_sources=["vector_document", "structured_sql", "web_search"],
        sub_queries={
            "vector_document": "document benchmark findings",
            "structured_sql": "How many documents are indexed?",
            "web_search": "latest external AI benchmarks",
        },
    )

    orchestrator = RoutingOrchestrator(
        classifier=mock_classifier,
        vector_handler=mock_vector_handler,
        sql_handler=mock_sql_handler,
        web_handler=mock_web_handler,
    )

    evidence, decision, meta = orchestrator.route_and_retrieve(
        query="Compare internal benchmarks with latest web benchmarks",
        routing_mode=RoutingMode.AUTO,
    )

    assert decision.route == RouteCategory.MULTI_SOURCE
    assert len(evidence) == 3
    source_types = {e.source_type for e in evidence}
    assert source_types == {"vector_document", "structured_sql", "web_search"}
    assert len(meta["sources_queried"]) == 3
    assert len(meta["failed_sources"]) == 0


def test_orchestrator_partial_failure_tolerance(mock_classifier, mock_vector_handler, mock_sql_handler, mock_web_handler):
    """RoutingOrchestrator must tolerate partial failure (e.g. web search error) without aborting other sources."""
    mock_classifier.classify.return_value = RoutingDecision(
        route=RouteCategory.MULTI_SOURCE,
        confidence=0.90,
        reasoning="Compound query requiring multi-source synthesis.",
        classification_method="logical_rule",
        selected_strategy=RetrievalStrategy.HYBRID,
        required_sources=["vector_document", "structured_sql", "web_search"],
    )

    # Simulate web search throwing an unexpected connection error
    mock_web_handler.execute.side_effect = RuntimeError("DNS resolution timeout")

    orchestrator = RoutingOrchestrator(
        classifier=mock_classifier,
        vector_handler=mock_vector_handler,
        sql_handler=mock_sql_handler,
        web_handler=mock_web_handler,
    )

    evidence, decision, meta = orchestrator.route_and_retrieve(
        query="Compare document findings with online benchmarks",
    )

    # Vector and SQL evidence must still be returned!
    assert len(evidence) == 2
    assert {"vector_document", "structured_sql"} == {e.source_type for e in evidence}
    assert len(meta["failed_sources"]) == 1
    assert "web_search" in meta["failed_sources"][0]
