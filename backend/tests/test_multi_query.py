"""Unit tests for Multi-Query retriever."""

from backend.app.embeddings.base import BaseEmbeddings
from backend.app.generation.ollama_client import OllamaClient
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.retrieval.multi_query import MultiQueryRetriever
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.storage.qdrant_client import QdrantStorageManager


def test_multi_query_retriever(
    test_pipeline: IngestionPipeline,
    test_storage: QdrantStorageManager,
    mock_embeddings: BaseEmbeddings,
    sample_txt_path,
):
    test_pipeline.ingest_from_path(sample_txt_path, doc_id="mq_doc")

    dense = SimilarityRetriever(
        storage_manager=test_storage,
        embedding_model=mock_embeddings,
        collection_name="test_collection",
    )
    ollama = OllamaClient(base_url="http://localhost:99999", enable_fallback=True)

    mq = MultiQueryRetriever(
        base_retriever=dense,
        ollama_client=ollama,
        num_queries=3,
        rrf_k=60,
    )

    results = mq.retrieve(query="What is autonomous agent architecture?", top_k=2)
    assert len(results) > 0
    assert len(mq.last_generated_queries) >= 2
    # Verify the original query is in the list
    assert mq.last_generated_queries[0] == "What is autonomous agent architecture?"
    assert results[0].retrieval_method == "multi_query_fusion"
