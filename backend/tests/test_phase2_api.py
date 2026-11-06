"""Integration tests for Phase 2 API endpoints, strategies, and backward compatibility."""

from pathlib import Path
from fastapi.testclient import TestClient


def test_api_multi_strategy_and_metadata(
    client: TestClient,
    sample_pdf_path: Path,
    sample_txt_path: Path,
):
    # Ingest test documents
    with sample_pdf_path.open("rb") as f:
        res = client.post(
            "/api/v1/documents/upload",
            files={"file": (sample_pdf_path.name, f, "application/pdf")},
        )
        assert res.status_code == 201

    with sample_txt_path.open("rb") as f:
        res = client.post(
            "/api/v1/documents/upload",
            files={"file": (sample_txt_path.name, f, "text/plain")},
        )
        assert res.status_code == 201

    # 1. Test Baseline Strategy (Backward Compatible)
    legacy_payload = {"query": "What is RAG?"}
    res = client.post("/api/v1/chat", json=legacy_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["grounded"] is True
    assert data["retrieval_metadata"]["strategy"] == "baseline"

    # 2. Test Hybrid Retrieval Strategy
    hybrid_payload = {
        "query": "How do agents perceive their environment through sensors?",
        "retrieval_strategy": "hybrid",
        "top_k": 3,
    }
    res = client.post("/api/v1/chat", json=hybrid_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["retrieval_metadata"]["strategy"] == "hybrid"
    assert data["retrieval_metadata"]["fusion_applied"] is True
    assert len(data["retrieved_chunks"]) > 0

    # 3. Test Multi-Query Strategy
    mq_payload = {
        "query": "What are the components of memory systems in AI?",
        "retrieval_strategy": "multi_query",
        "top_k": 2,
    }
    res = client.post("/api/v1/chat", json=mq_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["retrieval_metadata"]["strategy"] == "multi_query"
    assert len(data["retrieval_metadata"]["generated_queries"]) > 0

    # 4. Test HyDE Strategy
    hyde_payload = {
        "query": "How is vector indexing configured in Qdrant?",
        "retrieval_strategy": "hyde",
        "top_k": 2,
    }
    res = client.post("/api/v1/chat", json=hyde_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["retrieval_metadata"]["strategy"] == "hyde"
    assert data["retrieval_metadata"]["hypothetical_document"] is not None

    # 5. Test Decomposition Strategy
    decomp_payload = {
        "query": "What is agent memory and how are tools integrated?",
        "retrieval_strategy": "decomposition",
        "top_k": 3,
    }
    res = client.post("/api/v1/chat", json=decomp_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["retrieval_metadata"]["strategy"] == "decomposition"
    assert len(data["retrieval_metadata"]["sub_queries"]) >= 1

    # 6. Test Metadata Filtering (restrict to PDF only)
    filter_payload = {
        "query": "What is described on page 2?",
        "retrieval_strategy": "baseline",
        "filters": {"filename": sample_pdf_path.name},
        "top_k": 2,
    }
    res = client.post("/api/v1/chat", json=filter_payload)
    assert res.status_code == 200
    data = res.json()
    for chunk in data["retrieved_chunks"]:
        assert chunk["filename"] == sample_pdf_path.name
