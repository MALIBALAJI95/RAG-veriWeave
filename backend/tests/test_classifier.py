"""Tests for query signal analysis, logical route classification, user overrides, and fallback."""

import pytest
from backend.app.routing.classifier import RouteClassifier
from backend.app.routing.query_analyzer import QueryAnalyzer
from backend.app.routing.schemas import RouteCategory, RoutingDecision, RoutingMode
from backend.app.schemas.chat import RetrievalStrategy


def test_query_analyzer_signals():
    """QueryAnalyzer must accurately detect SQL, web, multi-source, and entity signals."""
    analyzer = QueryAnalyzer()

    # SQL signals
    sig_sql = analyzer.analyze("How many total documents are indexed in the database?")
    assert sig_sql.has_sql_keywords is True
    assert sig_sql.has_web_keywords is False

    # Web signals
    sig_web = analyzer.analyze("What are the latest 2026 features released in LangChain?")
    assert sig_web.has_web_keywords is True
    assert sig_web.web_intent_score > 0.0

    # Multi-source indicators
    sig_multi = analyzer.analyze("Compare the findings in our uploaded report with the latest web standards")
    assert sig_multi.has_multi_source_indicators is True

    # Exact identifiers (e.g., UUID or filename)
    sig_doc = analyzer.analyze("Show details for report_q3_final.pdf")
    assert sig_doc.has_exact_identifiers is True


def test_route_classifier_logical_rules():
    """RouteClassifier must logically classify queries with high confidence without LLM inference."""
    classifier = RouteClassifier(confidence_threshold=0.65)

    # 1. SQL metadata questions
    res_sql = classifier.classify("How many documents are uploaded in the system?")
    assert res_sql.route == RouteCategory.STRUCTURED_SQL
    assert res_sql.confidence >= 0.85
    assert res_sql.classification_method == "logical_rule"

    # 2. Web search queries
    res_web = classifier.classify("What are the latest updates and breaking news in Python 3.13?")
    assert res_web.route == RouteCategory.WEB_SEARCH
    assert res_web.confidence >= 0.85
    assert res_web.classification_method == "logical_rule"

    # 3. Multi-source compound questions
    res_multi = classifier.classify("Compare our internal document benchmarks with latest external web benchmarks")
    assert res_multi.route == RouteCategory.MULTI_SOURCE
    assert res_multi.confidence >= 0.85
    assert "vector_document" in res_multi.required_sources
    assert "web_search" in res_multi.required_sources

    # 4. Standard semantic document questions
    res_doc = classifier.classify("What is the primary methodology described in the document?")
    assert res_doc.route == RouteCategory.VECTOR_DOCUMENT
    assert res_doc.confidence >= 0.70


def test_route_classifier_user_overrides():
    """RouteClassifier must strictly respect explicit user RoutingMode overrides."""
    classifier = RouteClassifier()

    # Even a question with SQL keywords must route to document if DOCUMENT_ONLY requested
    res_doc = classifier.classify(
        query="How many total documents are there?",
        routing_mode=RoutingMode.DOCUMENT_ONLY,
    )
    assert res_doc.route == RouteCategory.VECTOR_DOCUMENT
    assert res_doc.classification_method == "user_override"
    assert res_doc.confidence == 1.0

    # Even a question about PDF content must route to SQL if SQL_ONLY requested
    res_sql = classifier.classify(
        query="Explain the neural attention mechanism",
        routing_mode=RoutingMode.SQL_ONLY,
    )
    assert res_sql.route == RouteCategory.STRUCTURED_SQL
    assert res_sql.classification_method == "user_override"

    # WEB_ONLY override
    res_web = classifier.classify(
        query="Summarize chapter 1",
        routing_mode=RoutingMode.WEB_ONLY,
    )
    assert res_web.route == RouteCategory.WEB_SEARCH
    assert res_web.classification_method == "user_override"

    # MULTI_SOURCE override
    res_ms = classifier.classify(
        query="What is transformer architecture?",
        routing_mode=RoutingMode.MULTI_SOURCE,
    )
    assert res_ms.route == RouteCategory.MULTI_SOURCE
    assert res_ms.classification_method == "user_override"


def test_route_classifier_fallback():
    """RouteClassifier must execute safe fallback to document retrieval for ambiguous low-confidence queries."""
    # Instantiating with a high confidence threshold forces fallback for ambiguous queries
    classifier = RouteClassifier(confidence_threshold=0.99)

    res = classifier.classify("hello there")
    assert res.route == RouteCategory.VECTOR_DOCUMENT
    assert res.fallback_triggered is True
    assert res.classification_method == "confidence_fallback"
