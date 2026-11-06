"""Integration tests for FastAPI endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "VeriWeave"
    assert "/docs" in data["docs"]


def test_health_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "components" in data
    assert "vector_storage" in data["components"]
    assert "embeddings" in data["components"]
    assert "llm_engine" in data["components"]
    assert data["components"]["vector_storage"]["status"] == "ok"


def test_document_crud_and_chat_flow(
    client: TestClient,
    sample_pdf_path: Path,
    sample_txt_path: Path,
):
    # 1. Upload TXT document
    with sample_txt_path.open("rb") as f:
        res = client.post(
            "/api/v1/documents/upload",
            files={"file": (sample_txt_path.name, f, "text/plain")},
        )
    assert res.status_code == 201, res.text
    txt_data = res.json()
    txt_doc_id = txt_data["doc_id"]
    assert txt_data["filename"] == sample_txt_path.name
    assert txt_data["chunk_count"] > 0
    assert txt_data["status"] == "indexed"

    # 2. Upload PDF document
    with sample_pdf_path.open("rb") as f:
        res = client.post(
            "/api/v1/documents/upload",
            files={"file": (sample_pdf_path.name, f, "application/pdf")},
        )
    assert res.status_code == 201, res.text
    pdf_data = res.json()
    pdf_doc_id = pdf_data["doc_id"]
    assert pdf_data["page_count"] == 2
    assert pdf_data["chunk_count"] >= 2

    # 3. List documents
    res = client.get("/api/v1/documents")
    assert res.status_code == 200
    list_data = res.json()
    assert list_data["total"] == 2
    doc_ids = [d["doc_id"] for d in list_data["documents"]]
    assert txt_doc_id in doc_ids
    assert pdf_doc_id in doc_ids

    # 4. Get specific document chunks
    res = client.get(f"/api/v1/documents/{pdf_doc_id}")
    assert res.status_code == 200
    chunks = res.json()
    assert len(chunks) >= 2
    assert chunks[0]["page_number"] in [1, 2]
    assert chunks[0]["doc_id"] == pdf_doc_id

    # 5. Query chat endpoint
    chat_payload = {
        "query": "How does RAG balance parametric knowledge?",
        "top_k": 3,
    }
    chat_res = client.post("/api/v1/chat", json=chat_payload)
    assert chat_res.status_code == 200, chat_res.text
    chat_data = chat_res.json()
    assert chat_data["query"] == chat_payload["query"]
    assert len(chat_data["answer"]) > 0
    assert len(chat_data["citations"]) > 0
    # Verify citations have page references
    citation = chat_data["citations"][0]
    assert "page_number" in citation
    assert "filename" in citation
    assert "score" in citation
    assert chat_data["latency_ms"] > 0

    # 6. Delete TXT document
    del_res = client.delete(f"/api/v1/documents/{txt_doc_id}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "deleted"
    assert del_data["doc_id"] == txt_doc_id

    # 7. Verify deletion reflected in list
    res = client.get("/api/v1/documents")
    assert res.status_code == 200
    updated_list = res.json()
    assert updated_list["total"] == 1
    assert updated_list["documents"][0]["doc_id"] == pdf_doc_id


def test_upload_unsupported_file_type(client: TestClient):
    fake_content = b"Binary executable content"
    res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("malware.exe", fake_content, "application/octet-stream")},
    )
    assert res.status_code == 415
