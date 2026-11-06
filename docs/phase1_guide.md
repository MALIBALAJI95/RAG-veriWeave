# VeriWeave Phase 1 — Implementation & Verification Guide

## 1. Phase 1 Objectives
The goal of Phase 1 is to build an original, modular, scalable, and verifiable end-to-end baseline RAG pipeline:
1. Multi-format ingestion: PDF, DOCX, and TXT parsing with page-level text extraction.
2. Recursive chunking: Hierarchy-based splitting (`\n\n`, `\n`, sentence, words) preserving page numbers, character offsets, and document identifiers.
3. Dense local embeddings: Using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) on Apple Silicon CPU/MPS.
4. Persistent Qdrant vector storage: On-disk persistence (`./data/qdrant_storage`) ensuring indexed documents survive application restarts.
5. Similarity retrieval: Dense cosine similarity query retrieval with score filtering.
6. Local Ollama LLM integration: Grounded response synthesis with citation formatting (`[Doc: <filename>, Page: <page>]`) and resilient fallback mode.
7. REST API services: FastAPI endpoints for upload, document management, chat, and system health.
8. Comprehensive automated test suite: 100% test coverage for all Phase 1 components.

---

## 2. API Endpoints Reference

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/documents/upload` | Upload & index document (PDF, DOCX, TXT, MD) | `201 Created` |
| `GET` | `/api/v1/documents` | List all indexed documents with page & chunk stats | `200 OK` |
| `GET` | `/api/v1/documents/{doc_id}` | Retrieve all chunks and metadata for a document | `200 OK` |
| `DELETE`| `/api/v1/documents/{doc_id}` | Delete document chunks from Qdrant and file from disk | `200 OK` |
| `POST` | `/api/v1/chat` | Semantic retrieval + grounded generation with citations | `200 OK` |
| `GET` | `/api/v1/health` | Diagnostics for vector storage, embeddings & Ollama | `200 OK` |

---

## 3. Step-by-Step Execution Guide

### 3.1 Setup Environment
```bash
# Create virtual environment with Python 3.12
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3.2 Run Automated Tests
```bash
.venv/bin/pytest backend/tests -v
```

Expected output:
```text
backend/tests/test_api.py::test_root_endpoint PASSED
backend/tests/test_api.py::test_health_endpoint PASSED
backend/tests/test_api.py::test_document_crud_and_chat_flow PASSED
backend/tests/test_api.py::test_upload_unsupported_file_type PASSED
backend/tests/test_chunking.py::test_chunker_basic PASSED
backend/tests/test_chunking.py::test_chunker_multi_page_preserves_page_numbers PASSED
backend/tests/test_chunking.py::test_chunker_invalid_overlap PASSED
backend/tests/test_chunking.py::test_chunker_empty_pages PASSED
backend/tests/test_embeddings.py::test_mock_embeddings PASSED
backend/tests/test_embeddings.py::test_sentence_transformer_embeddings_real PASSED
backend/tests/test_generation.py::test_format_context_blocks PASSED
backend/tests/test_generation.py::test_fallback_grounded_generator PASSED
backend/tests/test_generation.py::test_generator_no_chunks PASSED
backend/tests/test_ingestion.py::test_pdf_loader_multi_page PASSED
backend/tests/test_ingestion.py::test_docx_loader PASSED
backend/tests/test_ingestion.py::test_txt_loader PASSED
backend/tests/test_ingestion.py::test_loader_factory PASSED
backend/tests/test_ingestion.py::test_loader_factory_unsupported PASSED
backend/tests/test_ingestion.py::test_pdf_loader_missing_file PASSED
backend/tests/test_retrieval.py::test_similarity_retriever PASSED
backend/tests/test_storage.py::test_qdrant_lifecycle_and_persistence PASSED
============================== 21 passed in 0.29s ==============================
```

### 3.3 Execute Live Verification
```bash
.venv/bin/python3 backend/tests/verify_phase1_live.py
```

### 3.4 Launch FastAPI Server
```bash
.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger UI is accessible at: `http://localhost:8000/docs`

---

## 4. Verification Checkpoints Completed
- [x] Ingest multi-page PDF (`pypdf`), preserving page numbers.
- [x] Ingest formatted DOCX (`python-docx`), extracting paragraphs and tables.
- [x] Ingest plain text (`.txt`, `.md`).
- [x] Recursive chunker respecting chunk size and overlap, with token and offset metadata.
- [x] Sentence-Transformers `all-MiniLM-L6-v2` embedding generation (384 dimensions).
- [x] Persistent Qdrant vector database on disk (`./data/qdrant_storage`).
- [x] Cross-restart persistence verified: documents remain indexed and searchable.
- [x] Semantic similarity retrieval with top-k and score thresholding.
- [x] Ollama client with grounded prompt formulation and resilient fallback generator.
- [x] Inline source citation attribution (`[Doc: <filename>, Page: <page>]`).
- [x] REST API endpoints (`/documents/upload`, `/documents`, `/chat`, `/health`).
- [x] 21 automated unit and integration tests passing.
