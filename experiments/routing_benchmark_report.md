# VeriWeave Phase 3: Routing Benchmark Report

**Generated**: 2026-11-06 11:20:21 UTC  
**Platform**: VeriWeave — Adaptive Multi-Strategy Retrieval and Grounded Generation Engine  
**Tagline**: *Retrieve intelligently. Reason contextually. Respond reliably.*  
**Dataset**: 25 evaluation queries across 4 routes (`vector_document`, `structured_sql`, `web_search`, `multi_source`)

---

## 1. Executive Summary

| Routing Strategy | Accuracy | Macro F1 | Avg Latency (ms) | P95 Latency (ms) | Fallback Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Pure Logical Heuristics** | **100.0%** | **1.0000** | **0.06 ms** | **0.10 ms** | 4.0% |
| **VeriWeave Adaptive Hybrid** | **100.0%** | **1.0000** | **0.73 ms** | **0.05 ms** | 4.0% |

---

## 2. Per-Category Breakdown (Adaptive Hybrid)

| Route Category | Support | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: |
| `vector_document` | 7 | 1.0000 | 1.0000 | **1.0000** |
| `structured_sql` | 6 | 1.0000 | 1.0000 | **1.0000** |
| `web_search` | 6 | 1.0000 | 1.0000 | **1.0000** |
| `multi_source` | 6 | 1.0000 | 1.0000 | **1.0000** |

---

## 3. Confusion Matrix (Adaptive Hybrid)

| True \ Predicted | vector_document | structured_sql | web_search | multi_source |
| :--- | :---: | :---: | :---: | :---: |
| `vector_document` | 7 | 0 | 0 | 0 |
| `structured_sql` | 0 | 6 | 0 | 0 |
| `web_search` | 0 | 0 | 6 | 0 |
| `multi_source` | 0 | 0 | 0 | 6 |

---

## 4. Architectural Analysis & Key Findings

1. **Near-Zero Latency Routing**: The logical fast-path resolves high-confidence queries in less than 0.2ms without requiring expensive LLM network inference.
2. **High Precision on Structured SQL**: Exact regex and schema keyword patterns achieve 100% precision on catalog metadata questions.
3. **Multi-Source Disambiguation**: Compound queries combining document concepts and current/external data are accurately partitioned into independent sub-queries.
4. **Safe Fallback Guarantees**: Ambiguous queries below the 0.65 confidence threshold trigger safe fallback to vector document retrieval, eliminating hard errors.
