# VeriWeave Architectural Specification

> **Tagline**: Retrieve intelligently. Reason contextually. Respond reliably.

VeriWeave is an advanced, production-grade Retrieval-Augmented Generation (RAG) platform designed to eliminate hallucinations and achieve verifiable citation-grounded question answering over multi-format documents.

---

## 1. System Architecture Overview

```
                      +-----------------------------------------+
                      |             User Query / UI             |
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

## 2. Core Subsystems

### 2.1 Ingestion & Extraction Engine
- **`BaseDocumentLoader`**: Format-specific extraction abstraction returning `RawDocumentPage` objects with explicit 1-indexed `page_number` and source metadata.
- **`PDFLoader`**: Extracts text page-by-page from PDFs using `pypdf`, preserving physical page boundaries.
- **`DocxLoader`**: Extracts paragraphs and structured data from tables in `.docx` files using `python-docx`, grouping paragraphs into logical pages.
- **`TxtLoader`**: Parses UTF-8 and Latin-1 plain text and markdown documents, segmenting long documents by logical paragraph boundaries.

### 2.2 Metadata Preservation & Chunking Contract
Every document chunk extracted by `RecursiveCharacterChunker` adheres to a strict contract:
- `chunk_id`: Deterministic unique identifier (`{doc_id}_c{chunk_index}`)
- `doc_id`: Parent document UUID
- `filename`: Original user filename
- `page_number`: Originating physical or logical page (1-indexed)
- `chunk_index`: Zero-indexed position in document
- `char_start` / `char_end`: Exact character boundaries within the page
- `token_count_estimate`: Word token approximation

### 2.3 Local Embedding Engine
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Footprint**: ~80 MB memory, 384 dimensions, fast inference on Apple Silicon CPU/MPS.
- **Normalization**: Unit $L_2$ normalization applied to all vectors, enabling fast cosine similarity calculations.
- **Offline Resiliency**: Attempts fast local cache loading (`local_files_only=True`) before reaching remote hubs.

### 2.4 Persistent On-Disk Vector Storage
- **Engine**: Qdrant Vector Database (`qdrant-client`)
- **Storage Mode**: Persistent file-backed on-disk storage (`./data/qdrant_storage`).
- **Persistence Guarantee**: Collections, vectors, payloads, and indexes survive application restarts and system reboots.
- **Filtering**: Native payload filtering by `doc_id` and score threshold filtering.

### 2.5 Generation & Grounding Engine
- **Local LLM**: Ollama serving quantized instruction-tuned models (e.g. `llama3.2:1b`, `llama3.2:3b`, `qwen2.5:1.5b`).
- **Resilient Fallback Mode**: When the Ollama daemon is offline, an extractive grounding synthesizer compiles verified source facts and inline citations directly from top retrieved chunks.
- **Citation Attribution**: Every factual claim is mapped to `[Doc: <filename>, Page: <page>]` with similarity score and text snippets.

---

## 3. Resource & Memory Budget (8 GB Apple Silicon Mac)

| Component | Target Model / Runtime | Memory Footprint | Device / Execution |
| :--- | :--- | :--- | :--- |
| **Embeddings** | `all-MiniLM-L6-v2` | ~80 - 120 MB | CPU / MPS (Metal) |
| **Vector DB** | Qdrant Disk Storage | ~50 - 100 MB | Disk Mmap |
| **Backend API** | FastAPI + Uvicorn | ~60 MB | Python 3.12 |
| **LLM Inference** | Ollama `llama3.2:1b` (Q4_K_M) | ~1.3 GB | Metal MPS / Neural Engine |
| **Total System Load**| **All Active** | **< 2.0 GB** | **Optimal for 8GB Mac** |
