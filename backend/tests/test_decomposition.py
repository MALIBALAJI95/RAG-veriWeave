"""Unit tests for Query Decomposition retriever."""

from backend.app.embeddings.base import BaseEmbeddings
from backend.app.generation.ollama_client import OllamaClient
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.retrieval.decomposition import QueryDecompositionRetriever
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.storage.qdrant_client import QdrantStorageManager


def test_query_decomposition(
    test_pipeline: IngestionPipeline,
    test_storage: QdrantStorageManager,
    mock_embeddings: BaseEmbeddings,
    sample_txt_path,
):
    test_pipeline.ingest_from_path(sample_txt_path, doc_id="decomp_doc")

    dense = SimilarityRetriever(
        storage_manager=test_storage,
        embedding_model=mock_embeddings,
        collection_name="test_collection",
    )
    ollama = OllamaClient(base_url="http://localhost:99999", enable_fallback=True)

    decomp = QueryDecompositionRetriever(
        base_retriever=dense,
        ollama_client=ollama,
        max_subqueries=3,
        rrf_k=60,
    )

    compound_query = "What is agent short-term memory and how does long-term memory work?"
    subqueries = decomp.decompose(compound_query)
    assert len(subqueries) >= 2

    results = decomp.retrieve(query=compound_query, top_k=2)
    assert len(results) > 0
    assert results[0].doc_id == "decomp_doc"
    assert results[0].retrieval_method == "query_decomposition"
