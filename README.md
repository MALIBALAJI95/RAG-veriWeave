# VeriWeave — Adaptive Multi-Strategy Retrieval and Grounded Generation Engine

> *"Retrieve intelligently. Reason contextually. Respond reliably."*

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Persistent%20Disk-red.svg)](https://qdrant.tech/)
[![HuggingFace](https://img.shields.io/badge/Sentence--Transformers-all--MiniLM--L6--v2-yellow.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![CrossEncoder](https://img.shields.io/badge/Cross--Encoder-ms--marco--MiniLM--L--6--v2-orange.svg)](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2)
[![Tests](https://img.shields.io/badge/Tests-36%2F36%20Passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 1. Project Overview

**VeriWeave** is an industry-standard, production-grade Retrieval-Augmented Generation (RAG) platform. It goes beyond conventional "toy" PDF Q&A demos by establishing an engineering foundation for:
- **Multi-Format Ingestion**: PDF, DOCX, TXT, and Markdown parsing with strict physical & logical page boundary tracking.
- **Recursive Hierarchical Chunking**: Splits text preserving character offsets, token counts, and parent document metadata.
- **Dense Local Embeddings**: `all-MiniLM-L6-v2` (384 dimensions) optimized for 8 GB RAM Apple Silicon Macs (CPU/MPS acceleration).
- **Persistent Qdrant Storage**: File-backed on-disk storage (`./data/qdrant_storage`), ensuring collections survive process restarts.
- **Advanced Multi-Strategy Retrieval (Phase 2)**:
  - **Baseline Dense Similarity**: Fast cosine distance nearest-neighbor search.
  - **Multi-Query Retrieval**: LLM-generated semantic query variants fused via Reciprocal Rank Fusion (RRF).
  - **Hypothetical Document Embeddings (HyDE)**: Synthesizes hypothetical reference passages and retrieves matching true document chunks.
  - **Query Decomposition**: Decomposes compound questions into atomic sub-queries and aggregates evidence.
  - **Lexical Sparse BM25**: Okapi BM25 index built over identical Qdrant chunk IDs to solve vocabulary mismatch.
  - **Hybrid Dense + Sparse**: Dual-channel retrieval fused via configurable Reciprocal Rank Fusion ($k=60$).
  - **Cross-Encoder Reranking**: High-precision joint cross-attention scoring using `ms-marco-MiniLM-L-6-v2` with sigmoid probability mapping.
  - **Metadata Filtering**: Scoped filtering across `doc_id`, `filename`, `page_number`, and custom key-value pairs.
- **Grounded Answer Generation**: Local Ollama LLMs (`llama3.2:1b`, `llama3.2:3b`) with an offline extractive fallback engine.
- **Verifiable Inline Citations**: Every claim is mapped to `[Doc: <filename>, Page: <page>]` with similarity scores and excerpts.
- **Comprehensive Benchmarks**: Quantitative evaluation comparing all strategies using Recall@K, Precision@K, MRR, and NDCG.

---

## 2. Multi-Strategy Architecture

```
                                  +-----------------------------------------+
                                  |         User Request / React UI         |
                                  +--------------------+--------------------+
                                                       |
                                                       v
                                  +-----------------------------------------+
                                  |        FastAPI REST API Gateway         |
                                  |   /upload   /documents   /chat  /health |
                                  +--------------------+--------------------+
                                                       |
            +------------------------------------------+-------------------------------------------+
            | (Ingestion Path)                                                                     | (Query Path)
            v                                                                                      v
+-----------------------+                                                      +---------------------------------------+
|  Document Loaders     |                                                      |         Retrieval Orchestrator        |
|  (PDF, DOCX, TXT, MD) |                                                      | Strategy: baseline | hybrid | hyde ... |
+-----------+-----------+                                                      +-------------------+-------------------+
            | Raw Pages                                                                            |
            v                                                 +--------------------+---------------+--------------------+
+-----------------------+                                     |                    |                    |               |
| Recursive Chunker     |                                     v                    v                    v               v
| (Preserves metadata & |                               +-----------+        +-----------+        +-----------+   +-----------+
|  page numbers)        |                               | MultiQuery|        |   HyDE    |        |   Dense   |   |   BM25    |
+-----------+-----------+                               | Expansion |        | Synthesis |        | Embedding |   |  Lexical  |
            | Chunks + Offsets                          +-----+-----+        +-----+-----+        +-----+-----+   +-----+-----+
            v                                                 |                    |                    |               |
+-----------------------+                                     +--------------------+--------------------+---------------+
| Dense Chunk Encoder   |                                                                  |
| (384-dim embeddings)  |                                                                  v
+-----------+-----------+                                                      +---------------------------------------+
            | Chunks + Embeddings                                              |    Reciprocal Rank Fusion Engine      |
            v                                                                  |      RRF(d) = sum( 1 / (k + rank) )   |
+-----------------------+                                                      +-------------------+-------------------+
| Persistent Qdrant     |<=========================================================================| (Vector Search)
| Vector Store (Disk)   |                                                                  |
+-----------------------+                                                                  v
                                                                               +---------------------------------------+
                                                                               |      Cross-Encoder Reranker           |
                                                                               |   (ms-marco-MiniLM-L-6-v2)            |
                                                                               +-------------------+-------------------+
                                                                                                   | Top-K Candidates
                                                                                                   v
                                                                               +---------------------------------------+
                                                                               |  Context Formatter & Grounding Engine |
                                                                               +-------------------+-------------------+
                                                                                                   | Prompt + Citations
                                                                                                   v
                                                                               +---------------------------------------+
                                                                               |      Ollama LLM / Grounded Fallback   |
                                                                               | (Answer + Verified [Doc, Page] Cit.)  |
                                                                               +---------------------------------------+
```

---

## 3. Empirical Retrieval Benchmark Results

Evaluated against 10 gold-standard queries across technical reference documents:

| Retrieval Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | NDCG@3 | NDCG@5 | Latency (ms) | Candidates |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Dense)** | 1.000 | 1.000 | 1.000 | 1.000 | 0.977 | 0.995 | 4.08 ms | 5.0 |
| **Multi-Query** | 1.000 | 1.000 | 1.000 | 1.000 | 0.977 | 0.995 | 17.29 ms | 5.0 |
| **HyDE** | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 8.70 ms | 5.0 |
| **Query Decomposition** | 1.000 | 1.000 | 1.000 | 1.000 | 0.977 | 0.995 | 7.34 ms | 5.0 |
| **RAG Fusion (RRF)** | 1.000 | 1.000 | 1.000 | 1.000 | 0.930 | 0.988 | 3.84 ms | 5.0 |
| **Hybrid (Dense+BM25)** | 1.000 | 1.000 | 1.000 | 1.000 | 0.930 | 0.984 | 3.98 ms | 5.0 |
| **Hybrid + Cross-Encoder** | 1.000 | 1.000 | 1.000 | 1.000 | 0.977 | 0.995 | 50.65 ms | 10.0 |

---

## 4. Quickstart Guide

### 4.1 Prerequisites & Installation
```bash
# Clone repository
git clone https://github.com/your-username/RAG-veriWeave.git
cd RAG-veriWeave

# Create virtual environment
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
cp .env.example .env
```

### 4.2 Run Automated Tests
```bash
.venv/bin/pytest backend/tests -v
```
All **36 tests pass in under 1 second** (`36 passed in 0.83s`).

### 4.3 Run Live Multi-Strategy Verification & Benchmarks
```bash
# Live verification across all 7 retrieval scenarios
.venv/bin/python3 backend/tests/verify_phase2_live.py

# Quantitative retrieval benchmark
.venv/bin/python3 experiments/benchmark_retrieval.py
```

### 4.4 Start Backend Server
```bash
.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 5. API Usage Examples (Phase 2 Strategies)

### 5.1 Hybrid Retrieval (Dense + BM25 with RRF)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the trade-offs of BM25 sparse retrieval vs dense embeddings?",
    "retrieval_strategy": "hybrid",
    "top_k": 2
  }'
```

### 5.2 Hybrid Retrieval with Cross-Encoder Reranking
```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the advantages and weaknesses of dense vs BM25 sparse retrieval?",
    "retrieval_strategy": "hybrid_rerank",
    "top_k": 2,
    "rerank": true
  }'
```

### 5.3 Scoped Metadata Filtering
```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is described on page 2 regarding Qdrant?",
    "retrieval_strategy": "baseline",
    "filters": {
      "filename": "rag_architectures.pdf",
      "page_number": 2
    },
    "top_k": 2
  }'
```

---

## 6. Project Roadmap

- [x] **Phase 1**: Ingestion (PDF, DOCX, TXT), Recursive Chunking, Metadata Preservation, Sentence Transformers, Persistent Qdrant, Similarity Retrieval, Ollama Grounded Generation, Source Citations, FastAPI Services, Automated Tests.
- [x] **Phase 2**: Advanced Query Transformation & Retrieval (Multi-Query, HyDE, Query Decomposition, RAG Fusion, RRF, Hybrid Dense + BM25 Sparse Search, Metadata Filtering, Cross-Encoder Reranking, Quantitative Benchmarking).
- [ ] **Phase 3**: Intelligent Multi-Path Query Routing (Semantic Routing, SQL Structured Database Routing, Safeguarded Query Execution).
- [ ] **Phase 4**: Adaptive & Corrective RAG with LangGraph (Document Relevance Grading, Query Rewriting, Hallucination Checking, Self-Correction Loops).
- [ ] **Phase 5**: Kaggle GPU Model Training & Fine-Tuning (Sentence Transformers Contrastive Learning / MultipleNegativesRankingLoss, Cross-Encoder Fine-Tuning, MRR / NDCG Evaluation).
- [ ] **Phase 6**: Quantitative Evaluation & Benchmarking (RAG Triad Metrics: Context Relevance, Groundedness, Answer Relevance, Latency Profiling).
- [ ] **Phase 7**: Full-Stack React + TypeScript UI & Docker Containerization.
