"""Unit tests for Hypothetical Document Embeddings (HyDE) retriever."""

from backend.app.embeddings.base import BaseEmbeddings
from backend.app.generation.ollama_client import OllamaClient
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.retrieval.hyde import HyDERetriever
from backend.app.storage.qdrant_client import QdrantStorageManager


def test_hyde_retriever(
    test_pipeline: IngestionPipeline,
    test_storage: QdrantStorageManager,
    mock_embeddings: BaseEmbeddings,
    sample_pdf_path,
):
    test_pipeline.ingest_from_path(sample_pdf_path, doc_id="hyde_pdf")

    ollama = OllamaClient(base_url="http://localhost:99999", enable_fallback=True)
    hyde = HyDERetriever(
        storage_manager=test_storage,
        embedding_model=mock_embeddings,
        ollama_client=ollama,
        collection_name="test_collection",
    )

    results = hyde.retrieve(query="What is parametric vs non-parametric knowledge in RAG?", top_k=2)
    assert len(results) > 0
    assert hyde.last_hypothetical_document is not None
    # Crucial requirement: hypothetical document is NOT presented as returned chunk text
    assert results[0].doc_id == "hyde_pdf"
    assert results[0].text != hyde.last_hypothetical_document
    assert results[0].retrieval_method == "hyde"
