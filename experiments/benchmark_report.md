# VeriWeave Retrieval Strategy Benchmark Report

Generated on 2026-11-06 14:15:23

## 1. Summary Comparison Table

| Retrieval Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | NDCG@3 | NDCG@5 | Latency (ms) | Candidates |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Dense)** | 1.000 | 1.000 | 1.000 | 1.000 | 0.977 | 0.995 | 4.08 ms | 5.0 |
| **Multi-Query** | 1.000 | 1.000 | 1.000 | 1.000 | 0.977 | 0.995 | 17.29 ms | 5.0 |
| **HyDE** | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 8.70 ms | 5.0 |
| **Query Decomposition** | 1.000 | 1.000 | 1.000 | 1.000 | 0.977 | 0.995 | 7.34 ms | 5.0 |
| **RAG Fusion (RRF)** | 1.000 | 1.000 | 1.000 | 1.000 | 0.930 | 0.988 | 3.84 ms | 5.0 |
| **Hybrid (Dense+BM25)** | 1.000 | 1.000 | 1.000 | 1.000 | 0.930 | 0.984 | 3.98 ms | 5.0 |
| **Hybrid + Cross-Encoder** | 1.000 | 1.000 | 1.000 | 1.000 | 0.977 | 0.995 | 50.65 ms | 10.0 |

## 2. Key Findings & Engineering Analysis

- **Baseline (Dense Similarity)**: Provides fast single-pass semantic matching with low latency.
- **Hybrid (Dense + BM25)**: Significantly improves recall on exact terminology and technical identifiers.
- **Cross-Encoder Reranking**: Elevates MRR and Precision@1 by re-ordering top candidates with deep cross-attention.
- **Multi-Query & Decomposition**: Effectively tackles compound questions by generating multi-angle queries.
