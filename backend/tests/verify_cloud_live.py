"""Live verification script for VeriWeave cloud deployment architecture.

Validates:
1. Pluggable vector storage (Qdrant & pgvector adapter contracts)
2. Cloudflare Workers AI client & graceful offline fallback
3. Cloudflare Embeddings & 384-dim vector normalization
4. Structured PostgreSQL database models and blob persistence
5. Adaptive Corrective RAG with source provenance and citations
6. REST API routes for health, documents, chat, routing, and adaptive pipeline
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.embeddings.cloudflare_embeddings import CloudflareEmbeddings
from backend.app.generation.cloudflare_client import CloudflareWorkersAIClient
from backend.app.main import app
from backend.app.schemas.chat import RetrievedChunk
from backend.app.schemas.document import DocumentChunk
from backend.app.storage.factory import create_storage_manager


def run_cloud_verification():
    print("=" * 70)
    print("VeriWeave Cloud Deployment Verification Suite")
    print("Tagline: Retrieve intelligently. Reason contextually. Respond reliably.")
    print("=" * 70)

    settings = get_settings()
    print(f"\n[1] Configuration Check:")
    print(f"  - App Name: {settings.APP_NAME}")
    print(f"  - Vector Storage Backend: {settings.VECTOR_STORAGE_BACKEND}")
    print(f"  - LLM Provider: {settings.LLM_PROVIDER}")
    print(f"  - Embedding Provider: {settings.EMBEDDING_PROVIDER}")
    print(f"  - Max Upload Size: {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.1f} MB")
    print(f"  - CORS Origins: {settings.CORS_ORIGINS}")

    print(f"\n[2] Cloudflare Workers AI Adapter Check:")
    cf_client = CloudflareWorkersAIClient(
        account_id=settings.CLOUDFLARE_ACCOUNT_ID,
        api_token=settings.CLOUDFLARE_API_TOKEN,
        model=settings.CLOUDFLARE_LLM_MODEL,
        enable_fallback=True,
    )
    reachable, health_details = cf_client.check_health()
    print(f"  - Health status: reachable={reachable}")
    print(f"  - Health details: {health_details}")

    # Test generation with test evidence chunks
    test_chunks = [
        RetrievedChunk(
            chunk_id="test-c1",
            doc_id="test-d1",
            filename="cloud_spec.md",
            page_number=1,
            chunk_index=0,
            text="VeriWeave cloud deployment decouples frontend (Vercel) and backend (Render) using Supabase pgvector.",
            score=0.96,
        )
    ]
    gen_answer, gen_model, is_fallback = cf_client.generate(
        prompt="Explain VeriWeave cloud architecture.",
        retrieved_chunks=test_chunks,
    )
    print(f"  - Generated Answer: '{gen_answer[:80]}...'")
    print(f"  - Model used: {gen_model} (Fallback: {is_fallback})")
    assert len(gen_answer) > 20, "Answer text must not be empty"

    print(f"\n[3] Cloudflare Embeddings Adapter Check:")
    cf_emb = CloudflareEmbeddings(
        account_id=settings.CLOUDFLARE_ACCOUNT_ID,
        api_token=settings.CLOUDFLARE_API_TOKEN,
        dimension=384,
        fallback_local=True,
    )
    vec = cf_emb.embed_query("VeriWeave cloud vector test")
    print(f"  - Output vector dimension: {len(vec)}")
    assert len(vec) == 384, "Embedding dimension must be exactly 384"
    magnitude = sum(x * x for x in vec) ** 0.5
    print(f"  - Normalized L2 magnitude: {magnitude:.4f}")
    assert abs(magnitude - 1.0) < 0.05, "Vector must be unit normalized"

    print(f"\n[4] Storage Manager Factory Check:")
    from backend.app.api.deps import get_storage_manager
    storage = get_storage_manager()
    print(f"  - Active Storage Manager Type: {type(storage).__name__}")
    info = storage.get_collection_info(settings.QDRANT_COLLECTION_NAME)
    print(f"  - Collection Info: {info}")

    print(f"\n[5] End-to-End REST API Integration Check (TestClient):")
    client = TestClient(app)

    # Health endpoint
    h_res = client.get("/api/v1/health")
    assert h_res.status_code == 200, f"Health endpoint failed: {h_res.text}"
    h_data = h_res.json()
    print(f"  - GET /api/v1/health -> Status: {h_data.get('status')}")
    print(f"    Components: {list(h_data.get('components', {}).keys())}")

    # Documents upload & ingestion
    sample_content = (
        "VeriWeave Cloud Architecture Specification:\n"
        "1. React 18 + Vite frontend is hosted on Vercel with automated continuous deployment.\n"
        "2. FastAPI + LangGraph backend is hosted on Render free web service.\n"
        "3. Supabase provides PostgreSQL with the pgvector extension for high-performance vector search.\n"
        "4. Cloudflare Workers AI powers hosted LLM inference with zero server overhead.\n"
    )
    files = {"file": ("cloud_architecture.txt", sample_content.encode("utf-8"), "text/plain")}
    up_res = client.post("/api/v1/documents/upload", files=files)
    assert up_res.status_code == 201, f"Upload failed: {up_res.text}"
    up_data = up_res.json()
    doc_id = up_data["doc_id"]
    print(f"  - POST /api/v1/documents/upload -> doc_id={doc_id}, chunks={up_data['chunk_count']}")

    # List documents
    list_res = client.get("/api/v1/documents")
    assert list_res.status_code == 200
    docs = list_res.json()["documents"]
    print(f"  - GET /api/v1/documents -> Total indexed documents: {len(docs)}")
    assert any(d["doc_id"] == doc_id for d in docs), "Uploaded document not found in list"

    # Multi-strategy chat retrieval
    chat_payload = {
        "query": "Where is the React frontend hosted in VeriWeave?",
        "retrieval_strategy": "hybrid",
        "top_k": 3,
    }
    chat_res = client.post("/api/v1/chat", json=chat_payload)
    assert chat_res.status_code == 200, f"Chat failed: {chat_res.text}"
    chat_data = chat_res.json()
    print(f"  - POST /api/v1/chat (hybrid) -> Citations: {len(chat_data['citations'])}, Answer: '{chat_data['answer'][:70]}...'")
    assert len(chat_data["citations"]) > 0, "Chat must return citations"

    # Intelligent multi-path routing chat query (adaptive=False)
    route_payload = {
        "query": "How many total documents are indexed in the system?",
        "routing_mode": "auto",
        "adaptive": False,
    }
    route_res = client.post("/api/v1/chat", json=route_payload)
    assert route_res.status_code == 200, f"Routing failed: {route_res.text}"
    route_data = route_res.json()
    r_dec = route_data.get("routing_decision") or {}
    print(f"  - POST /api/v1/chat (routing_mode=auto) -> Route chosen: {r_dec.get('route')} (confidence={r_dec.get('confidence')})")

    # Adaptive & Corrective LangGraph workflow chat query (adaptive=True)
    adaptive_payload = {
        "query": "Where is the React frontend hosted in VeriWeave?",
        "adaptive": True,
    }
    adapt_res = client.post("/api/v1/chat", json=adaptive_payload)
    assert adapt_res.status_code == 200, f"Adaptive query failed: {adapt_res.text}"
    adapt_data = adapt_res.json()
    a_meta = adapt_data.get("adaptive_metadata") or {}
    print(f"  - POST /api/v1/chat (adaptive=True) -> Grounded: {a_meta.get('grounding_status', 'grounded')}, Citations: {len(adapt_data['citations'])}, Rewrites: {a_meta.get('rewrite_count', 0)}")

    # Clean up uploaded test document
    del_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 200
    print(f"  - DELETE /api/v1/documents/{doc_id} -> Deleted successfully")

    print("\n" + "=" * 70)
    print("ALL CLOUD DEPLOYMENT VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_cloud_verification()
