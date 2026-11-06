"""Integration tests for Phase 3 Intelligent Multi-Path Query Routing API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient


def test_api_routing_and_sql_retrieval(
    client: TestClient,
    sample_pdf_path: Path,
):
    # 1. Ingest document so SQLite catalog contains indexed data
    with sample_pdf_path.open("rb") as f:
        res = client.post(
            "/api/v1/documents/upload",
            files={"file": (sample_pdf_path.name, f, "application/pdf")},
        )
        assert res.status_code == 201
        doc_id = res.json()["doc_id"]

    # 2. Test SQL Routing for document count question
    sql_payload = {
        "query": "How many documents are uploaded in the system?",
        "routing_mode": "auto",
    }
    res = client.post("/api/v1/chat", json=sql_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["grounded"] is True
    assert data["routing_decision"] is not None
    assert data["routing_decision"]["route"] == "structured_sql"
    assert data["routing_decision"]["confidence"] >= 0.85
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["filename"] == "Database: SQLite Catalog"
    assert len(data["evidence"]) >= 1
    assert data["evidence"][0]["source_type"] == "structured_sql"

    # 3. Test Web Search Routing for current information
    web_payload = {
        "query": "What are the latest 2026 features released in LangChain and LangGraph?",
        "routing_mode": "auto",
    }
    res = client.post("/api/v1/chat", json=web_payload)
    assert res.status_code == 200
    web_data = res.json()

    assert web_data["routing_decision"]["route"] == "web_search"
    assert web_data["routing_decision"]["confidence"] >= 0.85
    assert len(web_data["citations"]) >= 1
    assert "Web:" in web_data["citations"][0]["filename"]
    assert len(web_data["evidence"]) >= 1
    assert web_data["evidence"][0]["source_type"] == "web_search"

    # 4. Test Explicit Routing Override (SQL_ONLY)
    override_payload = {
        "query": "What is the primary methodology described in the document?",
        "routing_mode": "sql_only",
    }
    res = client.post("/api/v1/chat", json=override_payload)
    assert res.status_code == 200
    override_data = res.json()
    assert override_data["routing_decision"]["route"] == "structured_sql"
    assert override_data["routing_decision"]["classification_method"] == "user_override"

    # 5. Test Explicit Multi-Source Routing
    multi_payload = {
        "query": "What are the key findings and how many documents are indexed?",
        "routing_mode": "multi_source",
    }
    res = client.post("/api/v1/chat", json=multi_payload)
    assert res.status_code == 200
    multi_data = res.json()
    assert multi_data["routing_decision"]["route"] == "multi_source"
    assert len(multi_data["evidence"]) >= 2

    # 6. Test Backward Compatibility: Legacy Phase 1 payload
    legacy_payload = {
        "query": "What is the transformer architecture and attention mechanism?",
    }
    res = client.post("/api/v1/chat", json=legacy_payload)
    assert res.status_code == 200
    legacy_data = res.json()
    assert legacy_data["grounded"] is True
    assert legacy_data["routing_decision"]["route"] == "vector_document"
