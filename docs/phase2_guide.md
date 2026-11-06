# VeriWeave Phase 2 — Advanced Multi-Strategy Retrieval Guide

> **Tagline**: Retrieve intelligently. Reason contextually. Respond reliably.

## 1. Overview & Objectives
Phase 2 enhances VeriWeave from a single-strategy dense similarity system into an advanced, multi-strategy, grounded retrieval platform. It implements seven distinct retrieval strategies:
1. **Baseline Dense Retrieval**: High-speed single-pass semantic vector search in Qdrant using Sentence-Transformers `all-MiniLM-L6-v2`.
2. **Multi-Query Retrieval**: Expands a single user query into multiple diverse semantic perspectives using the local LLM to overcome distance-based embedding limitations, merging candidates via Reciprocal Rank Fusion (RRF).
3. **Hypothetical Document Embeddings (HyDE)**: Generates a hypothetical reference answer passage via LLM, embeds the hypothetical passage, and retrieves real source documents matching that vector. Hypothetical text is strictly isolated and never presented as verified source evidence.
4. **Query Decomposition**: Analyzes complex or compound multi-part questions, breaks them down into atomic sub-queries, retrieves supporting evidence for each, and fuses the results preserving source provenance.
5. **Reciprocal Rank Fusion (RRF)**: Combines candidate lists across queries or retrieval channels using the standard smoothing formula:
   $$\text{RRF\_Score}(d) = \sum_{r \in R} \frac{1}{k + \text{rank}_r(d)} \quad (k=60)$$
6. **Hybrid Dense + Sparse Retrieval**: Combines semantic embeddings (Qdrant) with lexical BM25 Okapi keyword search, resolving the vocabulary mismatch problem while retaining semantic recall.
7. **Cross-Encoder Reranking**: Evaluates top retrieved query-document candidate pairs with deep joint cross-attention using `cross-encoder/ms-marco-MiniLM-L-6-v2`, mapping logits to probabilities via sigmoid:
   $$\sigma(s) = \frac{1}{1 + e^{-s}}$$
8. **Rich Metadata Filtering**: Scopes retrieval by `doc_id`, `filename`, `page_number`, and custom key-value pairs across both vector and lexical retrieval engines.

---

## 2. API Reference & Request Specifications

### Endpoint: `POST /api/v1/chat`

#### Request Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `query` | `string` | *(Required)* | Natural language question (1 - 2000 characters). |
| `retrieval_strategy` | `string` | `"baseline"` | Strategy: `baseline`, `multi_query`, `hyde`, `decomposition`, `fusion`, `hybrid`, `hybrid_rerank`, `rerank`. |
| `top_k` | `integer` | `4` | Number of final chunks to return (1 - 20). |
| `score_threshold` | `float` | `null` | Minimum similarity score filter (0.0 to 1.0). |
| `rerank` | `boolean` | `false` | Apply cross-encoder reranking over retrieved candidate pool. |
| `filters` | `object` | `null` | Scoped metadata filtering: `{"doc_id": "...", "filename": "...", "page_number": 1, "custom": {...}}`. |
| `doc_id_filter` | `string` | `null` | *(Backward-compatible)* Document UUID filter. |

#### Structured Retrieval Metadata in Response (`retrieval_metadata`)
```json
{
  "strategy": "hybrid_rerank",
  "generated_queries": [],
  "hypothetical_document": null,
  "sub_queries": [],
  "fusion_applied": true,
  "reranking_applied": true,
  "raw_candidate_count": 10,
  "returned_candidate_count": 2,
  "retrieval_latency_ms": 36.5
}
```

---

## 3. Empirical Benchmark Results

Evaluated on 10 gold-standard queries across multi-page PDF, formatted DOCX, and TXT documents.

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

## 4. Verification Commands

```bash
# 1. Run all 36 automated unit & integration tests
.venv/bin/pytest backend/tests -v

# 2. Run live verification across all 7 retrieval scenarios
.venv/bin/python3 backend/tests/verify_phase2_live.py

# 3. Run quantitative retrieval benchmark suite
.venv/bin/python3 experiments/benchmark_retrieval.py
```
