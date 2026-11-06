# VeriWeave — Adaptive Multi-Strategy Retrieval and Grounded Generation Engine

> *"Retrieve intelligently. Reason contextually. Respond reliably."*

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Persistent%20Disk-red.svg)](https://qdrant.tech/)
[![HuggingFace](https://img.shields.io/badge/Sentence--Transformers-all--MiniLM--L6--v2-yellow.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![Tests](https://img.shields.io/badge/Tests-21%2F21%20Passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 1. Project Overview

**VeriWeave** is an industry-standard, production-grade Retrieval-Augmented Generation (RAG) platform. It goes beyond conventional "toy" PDF Q&A demos by establishing an engineering foundation for:
- Multi-format document ingestion (PDF, DOCX, TXT, Markdown) with strict physical & logical page boundary tracking.
- Recursive hierarchical chunking preserving character offsets, token counts, and source metadata.
- Lightweight local dense embedding generation (`all-MiniLM-L6-v2`, 384 dimensions) optimized for 8 GB RAM Apple Silicon Macs (CPU/MPS acceleration).
- Persistent on-disk vector storage via Qdrant (`./data/qdrant_storage`), ensuring collections survive process restarts.
- Grounded answer generation using local Ollama LLMs (`llama3.2:1b`, `llama3.2:3b`, `qwen2.5:1.5b`) with an offline extractive fallback engine.
- Verifiable inline source citations (`[Doc: <filename>, Page: <page>]`) linked to exact chunk snippets and similarity scores.
- Fully typed, validated FastAPI REST services with interactive Swagger/OpenAPI documentation.

---

## 2. System Architecture

```
                      +-----------------------------------------+
                      |         User Request / React UI         |
                      +--------------------+--------------------+
                                           |
                                           v
                      +-----------------------------------------+
                      |         FastAPI REST API Gateway        |
                      |   /upload   /documents   /chat  /health |
                      +--------------------+--------------------+
                                           |
            +------------------------------+-------------------------------+
            |                                                              |
            v (Ingestion Path)                                             v (Retrieval & Generation Path)
+-----------------------+                                      +-----------------------+
|  Document Loaders     |                                      | Dense Query Encoder   |
|  (PDF, DOCX, TXT, MD) |                                      | (Sentence-Transformers|
+-----------+-----------+                                      | all-MiniLM-L6-v2)     |
            | Raw Pages                                        +-----------+-----------+
            v                                                              | Query Vector
+-----------------------+                                                  |
| Recursive Chunker     |                                                  v
| (Preserves metadata & |                                      +-----------------------+
|  page numbers)        |                                      | Persistent Qdrant     |
+-----------+-----------+                                      | On-Disk Vector DB     |
            | Chunks + Offsets                                 +-----------+-----------+
            v                                                              | Top-K Matches
+-----------------------+                                                  v
| Dense Chunk Encoder   |                                      +-----------------------+
| (384-dim embeddings)  |                                      | Context Formatter &   |
+-----------+-----------+                                      | Grounding Engine      |
            | Chunks + Embeddings                              +-----------+-----------+
            v                                                              | Prompt + Context
+-----------------------+                                                  v
| Persistent Qdrant     |                                      +-----------------------+
| Vector Store (Disk)   +------------------------------------->| Ollama LLM / Fallback |
+-----------------------+                                      | (Grounded Answer +    |
                                                               |  Source Citations)    |
                                                               +-----------------------+
```

---

## 3. Repository Organization

```
RAG-veriWeave/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── documents.py    # Document upload, list, detail, delete
│   │   │   │   │   ├── chat.py         # Grounded RAG query endpoint
│   │   │   │   │   └── health.py       # Storage, embedding, LLM diagnostics
│   │   │   │   └── api.py              # API v1 router aggregator
│   │   │   └── deps.py                 # Dependency injection providers
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic Settings & environment config
│   │   │   ├── exceptions.py           # Domain exceptions & error handlers
│   │   │   └── logging.py              # Structured logging (Loguru)
│   │   ├── embeddings/
│   │   │   ├── base.py                 # Embedding model interface
│   │   │   └── sentence_transformer.py # Local Sentence-BERT wrapper (MPS/CPU)
│   │   ├── generation/
│   │   │   ├── grounded_generator.py   # Grounding & citation assembly
│   │   │   ├── ollama_client.py        # Ollama HTTP client & fallback synthesizer
│   │   │   └── prompts.py              # Strict grounding prompt templates
│   │   ├── ingestion/
│   │   │   ├── chunkers/
│   │   │   │   └── recursive_chunker.py # Recursive text splitter with metadata
│   │   │   ├── loaders/
│   │   │   │   ├── base.py             # RawDocumentPage abstraction
│   │   │   │   ├── docx_loader.py      # python-docx parser (paragraphs & tables)
│   │   │   │   ├── factory.py          # Format resolution & validation
│   │   │   │   ├── pdf_loader.py       # pypdf page-by-page extractor
│   │   │   │   └── txt_loader.py       # Plain text & markdown parser
│   │   │   └── pipeline.py             # End-to-end ingestion orchestrator
│   │   ├── retrieval/
│   │   │   ├── base.py                 # Retriever interface
│   │   │   └── similarity_retriever.py # Dense cosine similarity retriever
│   │   ├── schemas/
│   │   │   ├── chat.py                 # ChatRequest, ChatResponse, Citation
│   │   │   ├── document.py             # DocumentMetadata, Chunk, Responses
│   │   │   └── health.py               # ComponentStatus, HealthResponse
│   │   └── main.py                     # FastAPI application factory & lifespan
│   ├── tests/
│   │   ├── conftest.py                 # Isolated test fixtures & mock embeddings
│   │   ├── test_api.py                 # Integration tests for REST endpoints
│   │   ├── test_chunking.py            # Chunker & metadata preservation tests
│   │   ├── test_embeddings.py          # Sentence-Transformers tests
│   │   ├── test_generation.py          # Grounded generator & citation tests
│   │   ├── test_ingestion.py           # PDF, DOCX, TXT loader tests
│   │   ├── test_retrieval.py           # Similarity retrieval tests
│   │   ├── test_storage.py             # Persistent Qdrant & restart tests
│   │   └── verify_phase1_live.py       # End-to-end live verification script
│   └── requirements.txt                # Production Python dependencies
├── data/
│   ├── documents/                      # Local uploaded document repository
│   └── qdrant_storage/                 # Persistent on-disk Qdrant vector database
├── datasets/
│   └── sample_docs/                    # Benchmark sample documents (PDF, DOCX, TXT)
├── docker/                             # Docker & deployment configs
├── docs/
│   ├── architecture.md                 # System architecture specification
│   └── phase1_guide.md                 # Phase 1 technical & verification guide
├── experiments/                        # Benchmark results & tracking logs
├── exported_models/                    # Fine-tuned model weights
├── frontend/                           # React + TypeScript + Vite UI
├── training/
│   └── kaggle/                         # GPU training notebooks & scripts
├── .env.example                        # Template environment variables
├── .gitignore                          # Strict gitignore rules
├── pyproject.toml                      # Pytest and packaging configuration
└── README.md                           # Project documentation
```

---

## 4. Quickstart Guide

### 4.1 Prerequisites
- Apple Silicon Mac (or Linux / Windows with Python 3.10+)
- Python 3.12 (recommended)
- (Optional) [Ollama](https://ollama.ai) installed with `ollama run llama3.2:1b`

### 4.2 Installation
```bash
# Clone repository
git clone https://github.com/your-username/RAG-veriWeave.git
cd RAG-veriWeave

# Create virtual environment
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
```

### 4.3 Run Automated Tests
```bash
.venv/bin/pytest backend/tests -v
```
All **21 unit and integration tests** execute in under 0.5s:
```text
============================== 21 passed in 0.29s ==============================
```

### 4.4 Run Live End-to-End Verification
```bash
.venv/bin/python3 backend/tests/verify_phase1_live.py
```
This runs a complete live ingestion of PDF, DOCX, and TXT files, queries Qdrant with dense vectors, verifies grounded generation and citation formatting, and tests cross-restart persistence.

### 4.5 Start Backend Server
```bash
.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 5. API Reference & Examples

### 5.1 System Health
```bash
curl -s http://127.0.0.1:8000/api/v1/health | python3 -m json.tool
```
```json
{
    "app_name": "VeriWeave",
    "status": "ok",
    "version": "0.1.0",
    "components": {
        "vector_storage": {
            "status": "ok",
            "details": {
                "engine": "Qdrant (persistent disk)",
                "storage_path": "data/qdrant_storage",
                "collection": "veriweave_documents",
                "points_count": 7
            }
        },
        "embeddings": {
            "status": "ok",
            "details": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 384,
                "device": "cpu"
            }
        },
        "llm_engine": {
            "status": "ok",
            "details": {
                "configured_model": "llama3.2:1b",
                "fallback_active": true
            }
        }
    }
}
```

### 5.2 Upload Document
```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/upload \
  -F "file=@datasets/sample_docs/rag_architectures.pdf"
```
```json
{
    "doc_id": "beb0b1c7-8dd4-49d6-8857-bc1b69eff21b",
    "filename": "rag_architectures.pdf",
    "file_type": "pdf",
    "file_size_bytes": 2129,
    "page_count": 2,
    "chunk_count": 2,
    "status": "indexed",
    "message": "Document successfully extracted, chunked, embedded, and indexed."
}
```

### 5.3 Ask Question (Chat & Grounded Citations)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the trade-offs of BM25 sparse retrieval vs dense embeddings?",
    "top_k": 2
  }'
```
```json
{
    "query": "What are the trade-offs of BM25 sparse retrieval vs dense embeddings?",
    "answer": "Based on the retrieved source documents, here is the verified information:\n\n- Sparse Retrieval and Lexical Matching  Sparse retrieval algorithms like BM25 leverage term frequencies and inverse document frequencies. They excel at exact keyword matching, technical identifiers, and rare terms where dense embeddings might suffer from vocabulary mismatch... [Doc: retrieval_strategies.docx, Page: 1]\n- Advanced Retrieval Strategies in RAG  Dense Retrieval and Embedding Representations  Dense retrieval maps documents and queries into continuous semantic vector spaces using transformer models such as Sentence-BERT or BGE... [Doc: retrieval_strategies.docx, Page: 1]",
    "citations": [
        {
            "citation_id": 1,
            "doc_id": "4162968b-5937-4697-9c85-25b59c462fda",
            "filename": "retrieval_strategies.docx",
            "page_number": 1,
            "chunk_index": 1,
            "score": 0.6852,
            "snippet": "Sparse Retrieval and Lexical Matching  Sparse retrieval algorithms like BM25 leverage term frequencies and inverse document frequencies..."
        }
    ],
    "model_used": "llama3.2:1b",
    "latency_ms": 3.68,
    "grounded": true,
    "fallback_used": false
}
```

---

## 6. Project Roadmap

- [x] **Phase 1**: Ingestion (PDF, DOCX, TXT), Recursive Chunking, Metadata Preservation, Sentence Transformers, Persistent Qdrant, Similarity Retrieval, Ollama Grounded Generation, Source Citations, FastAPI Services, Automated Tests.
- [ ] **Phase 2**: Advanced Query Transformation & Retrieval (Multi-Query, HyDE, Query Decomposition, RAG Fusion, RRF, Hybrid Dense + BM25 Sparse Search, Cross-Encoder Reranking).
- [ ] **Phase 3**: Intelligent Multi-Path Query Routing (Semantic Routing, SQL Structured Database Routing, Safeguarded Query Execution).
- [ ] **Phase 4**: Adaptive & Corrective RAG with LangGraph (Document Relevance Grading, Query Rewriting, Hallucination Checking, Self-Correction Loops).
- [ ] **Phase 5**: Kaggle GPU Model Training & Fine-Tuning (Sentence Transformers Contrastive Learning / MultipleNegativesRankingLoss, Cross-Encoder Fine-Tuning, MRR / NDCG Evaluation).
- [ ] **Phase 6**: Quantitative Evaluation & Benchmarking (RAG Triad Metrics: Context Relevance, Groundedness, Answer Relevance, Latency Profiling).
- [ ] **Phase 7**: Full-Stack React + TypeScript UI & Docker Containerization.
