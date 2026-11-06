"""Unit tests for similarity retrieval."""

from backend.app.embeddings.base import BaseEmbeddings
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.storage.qdrant_client import QdrantStorageManager


def test_similarity_retriever(
    test_pipeline: IngestionPipeline,
    test_storage: QdrantStorageManager,
    mock_embeddings: BaseEmbeddings,
    sample_txt_path,
):
    # Ingest document first
    ingest_res = test_pipeline.ingest_from_path(sample_txt_path, doc_id="txt_doc_1")
    assert ingest_res.chunk_count > 0

    retriever = SimilarityRetriever(
        storage_manager=test_storage,
        embedding_model=mock_embeddings,
        collection_name="test_collection",
    )

    # Search
    results = retriever.retrieve(query="memory systems and vector databases", top_k=2)
    assert len(results) > 0
    assert len(results) <= 2
    assert results[0].doc_id == "txt_doc_1"
    assert results[0].filename == sample_txt_path.name
    assert results[0].page_number >= 1

    # Empty query
    empty_results = retriever.retrieve(query="   ")
    assert empty_results == []
