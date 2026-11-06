"""Unit tests for BM25 lexical sparse retriever."""

from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.retrieval.bm25 import BM25Retriever, tokenize_text
from backend.app.schemas.chat import MetadataFilter
from backend.app.storage.qdrant_client import QdrantStorageManager


def test_tokenize_text():
    tokens = tokenize_text("BM25 & TF-IDF: Are they fast? Yes!")
    assert tokens == ["bm25", "tf", "idf", "are", "they", "fast", "yes"]


def test_bm25_retrieval_and_filtering(
    test_pipeline: IngestionPipeline,
    test_storage: QdrantStorageManager,
    sample_txt_path,
    sample_pdf_path,
):
    # Ingest sample docs into test_storage
    test_pipeline.ingest_from_path(sample_txt_path, doc_id="doc_txt")
    test_pipeline.ingest_from_path(sample_pdf_path, doc_id="doc_pdf")

    bm25 = BM25Retriever(
        storage_manager=test_storage,
        collection_name="test_collection",
    )

    # Rebuild index
    count = bm25.build_index(force_rebuild=True)
    assert count > 0

    # Query for distinct keyword in txt doc: "autonomous" or "sensors"
    results = bm25.retrieve(query="autonomous agents sensors", top_k=3)
    assert len(results) > 0
    assert results[0].doc_id == "doc_txt"
    assert "autonomous" in results[0].text.lower()
    assert results[0].score > 0.0

    # Test doc_id filter
    pdf_results = bm25.retrieve(
        query="retrieval generation",
        top_k=5,
        filters=MetadataFilter(doc_id="doc_pdf"),
    )
    for r in pdf_results:
        assert r.doc_id == "doc_pdf"

    # Test filename filter
    txt_results = bm25.retrieve(
        query="memory",
        top_k=5,
        filters=MetadataFilter(filename="ai_agents_overview.txt"),
    )
    for r in txt_results:
        assert r.filename == "ai_agents_overview.txt"

    # Unrelated query returns empty list
    unrelated = bm25.retrieve(query="quantum superconduction cryogenics", top_k=2)
    assert unrelated == []
