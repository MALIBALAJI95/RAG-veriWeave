# VeriWeave Architectural Specification

> **Tagline**: Retrieve intelligently. Reason contextually. Respond reliably.

VeriWeave is an advanced, production-grade Retrieval-Augmented Generation (RAG) platform designed to eliminate hallucinations and achieve verifiable citation-grounded question answering over multi-format documents.

---

## 1. Multi-Strategy Architecture Diagram

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

### 2.3 Retrieval Subsystems
1. **Dense Semantic Retrieval**: Sentence-Transformers `all-MiniLM-L6-v2` (384 dimensions) with persistent Qdrant on-disk indexing.
2. **Lexical Sparse Retrieval**: BM25 Okapi inverted indexing constructed directly over persistent Qdrant chunks, ensuring exact chunk identifier parity.
3. **Multi-Query Retrieval**: Expands input query into 3 distinct semantic viewpoints via local LLM, retrieving across viewpoints and fusing candidates.
4. **Hypothetical Document Embeddings (HyDE)**: Generates a plausible hypothetical passage, encodes the hypothetical passage, and retrieves real chunks. Keeps hypothetical text strictly isolated from evidence.
5. **Query Decomposition**: Splits compound questions into atomic sub-queries, retrieving evidence for each.
6. **Reciprocal Rank Fusion (RRF)**: Fuses candidate lists with $RRF\_Score(d) = \sum_{r \in R} \frac{1}{k + rank_r(d)}$ with configurable $k=60$.
7. **Cross-Encoder Reranker**: Performs joint cross-attention scoring over top candidates using `cross-encoder/ms-marco-MiniLM-L-6-v2`.

### 2.4 Persistent On-Disk Vector Storage
- **Engine**: Qdrant Vector Database (`qdrant-client`)
- **Storage Mode**: Persistent file-backed on-disk storage (`./data/qdrant_storage`).
- **Persistence Guarantee**: Collections, vectors, payloads, and indexes survive application restarts and system reboots.
- **Filtering**: Native payload filtering by `doc_id`, `filename`, `page_number`, and custom attributes.

### 2.5 Generation & Grounding Engine
- **Local LLM**: Ollama serving quantized instruction-tuned models (e.g. `llama3.2:1b`, `llama3.2:3b`, `qwen2.5:1.5b`).
- **Resilient Fallback Mode**: When the Ollama daemon is offline, an extractive grounding synthesizer compiles verified source facts and inline citations directly from top retrieved chunks.
- **Citation Attribution**: Every factual claim is mapped to `[Doc: <filename>, Page: <page>]` with similarity score and text snippets.

---

## 3. Resource & Memory Budget (8 GB Apple Silicon Mac)

| Component | Target Model / Runtime | Memory Footprint | Device / Execution |
| :--- | :--- | :--- | :--- |
| **Embeddings** | `all-MiniLM-L6-v2` | ~80 - 120 MB | CPU / MPS (Metal) |
| **Cross-Encoder Reranker** | `ms-marco-MiniLM-L-6-v2` | ~80 - 120 MB | CPU (lazy loaded) |
| **Sparse Retrieval** | BM25 In-Memory Index | ~10 - 25 MB | RAM |
| **Vector DB** | Qdrant Disk Storage | ~50 - 100 MB | Disk Mmap |
| **Backend API** | FastAPI + Uvicorn | ~60 MB | Python 3.12 |
| **LLM Inference** | Ollama `llama3.2:1b` (Q4_K_M) | ~1.3 GB | Metal MPS / Neural Engine |
| **Total System Load**| **All Active** | **< 2.2 GB** | **Optimal for 8GB Mac** |
