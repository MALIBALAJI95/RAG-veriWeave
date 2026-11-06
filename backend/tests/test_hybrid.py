"""Unit tests for Hybrid (Dense + Sparse) retriever."""

from backend.app.embeddings.base import BaseEmbeddings
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.retrieval.bm25 import BM25Retriever
from backend.app.retrieval.hybrid import HybridRetriever
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.storage.qdrant_client import QdrantStorageManager


def test_hybrid_retriever(
    test_pipeline: IngestionPipeline,
    test_storage: QdrantStorageManager,
    mock_embeddings: BaseEmbeddings,
    sample_txt_path,
):
    test_pipeline.ingest_from_path(sample_txt_path, doc_id="hybrid_doc")

    dense = SimilarityRetriever(
        storage_manager=test_storage,
        embedding_model=mock_embeddings,
        collection_name="test_collection",
    )
    sparse = BM25Retriever(
        storage_manager=test_storage,
        collection_name="test_collection",
    )
    sparse.build_index(force_rebuild=True)

    hybrid = HybridRetriever(dense_retriever=dense, sparse_retriever=sparse, rrf_k=60)

    results = hybrid.retrieve(query="agents long-term memory", top_k=3)
    assert len(results) > 0
    assert results[0].doc_id == "hybrid_doc"
    assert results[0].retrieval_method == "hybrid_dense_bm25"
    assert "rrf_ranks" in results[0].metadata
