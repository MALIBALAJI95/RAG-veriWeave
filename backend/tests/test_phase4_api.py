"""Integration tests for Phase 4 Adaptive & Corrective RAG API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient


def test_api_adaptive_rag_endpoint(
    client: TestClient,
    sample_pdf_path: Path,
):
    # 1. Ingest document so Qdrant and SQLite contain knowledge
    with sample_pdf_path.open("rb") as f:
        res = client.post(
            "/api/v1/documents/upload",
            files={"file": (sample_pdf_path.name, f, "application/pdf")},
        )
        assert res.status_code == 201

    # 2. Test Adaptive RAG Chat (`adaptive=true`)
    adaptive_payload = {
        "query": "Can you please tell me about dense similarity search and vector embeddings?",
        "adaptive": True,
        "routing_mode": "auto",
    }
    res = client.post("/api/v1/chat", json=adaptive_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["grounded"] is True
    assert data["adaptive_metadata"] is not None
    assert data["adaptive_metadata"]["adaptive_applied"] is True
    assert data["adaptive_metadata"]["retrieved_evidence_count"] >= 1
    assert data["adaptive_metadata"]["relevant_evidence_count"] >= 1
    assert len(data["citations"]) >= 1
    assert any("route_query" in t for t in data["adaptive_metadata"]["workflow_trace"])
    assert any("grade_evidence" in t for t in data["adaptive_metadata"]["workflow_trace"])
    assert any("generate_answer" in t for t in data["adaptive_metadata"]["workflow_trace"])
    assert any("finalize_response" in t for t in data["adaptive_metadata"]["workflow_trace"])

    # 3. Test Backward Compatibility (`adaptive=false`)
    non_adaptive_payload = {
        "query": "What is dense retrieval?",
        "adaptive": False,
    }
    res_non_adaptive = client.post("/api/v1/chat", json=non_adaptive_payload)
    assert res_non_adaptive.status_code == 200
    non_adaptive_data = res_non_adaptive.json()
    assert non_adaptive_data["grounded"] is True
    assert non_adaptive_data["adaptive_metadata"] is None


def test_api_adaptive_rag_insufficient_evidence(
    client: TestClient,
):
    """Adaptive RAG must truthfully state insufficient context when asked about absent topics."""
    payload = {
        "query": "What is the quantum warp drive equation according to the uploaded files?",
        "adaptive": True,
        "routing_mode": "document_only",
    }
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["adaptive_metadata"] is not None
    assert data["adaptive_metadata"]["retrieval_attempts"] >= 1
    # Truthfully declares lack of information
    assert "insufficient" in data["answer"].lower() or "not contain sufficient" in data["answer"].lower() or "no relevant documents" in data["answer"].lower()
