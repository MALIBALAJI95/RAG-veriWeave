"""Unit tests for persistent Qdrant vector storage manager."""

from pathlib import Path
from backend.app.schemas.document import DocumentChunk
from backend.app.storage.qdrant_client import QdrantStorageManager


def test_qdrant_lifecycle_and_persistence(temp_dir: Path):
    storage_path = temp_dir / "persistent_qdrant"
    collection_name = "test_persistence_col"

    # 1. Initialize first manager session
    manager_session1 = QdrantStorageManager(storage_path=storage_path)
    manager_session1.ensure_collection(collection_name, vector_size=4)

    chunks = [
        DocumentChunk(
            chunk_id="docA_c0",
            doc_id="docA",
            filename="docA.txt",
            page_number=1,
            chunk_index=0,
            text="First chunk of docA about vectors.",
            char_start=0,
            char_end=35,
        ),
        DocumentChunk(
            chunk_id="docA_c1",
            doc_id="docA",
            filename="docA.txt",
            page_number=2,
            chunk_index=1,
            text="Second chunk of docA about neural networks.",
            char_start=36,
            char_end=79,
        ),
        DocumentChunk(
            chunk_id="docB_c0",
            doc_id="docB",
            filename="docB.txt",
            page_number=1,
            chunk_index=0,
            text="First chunk of docB about databases.",
            char_start=0,
            char_end=36,
        ),
    ]

    # Vectors for 4-dim space
    vectors = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
    ]

    upserted = manager_session1.upsert_chunks(collection_name, chunks, vectors)
    assert upserted == 3

    # Query in session 1
    query_vec = [1.0, 0.0, 0.0, 0.0]
    results = manager_session1.search_similar(collection_name, query_vec, top_k=2)
    assert len(results) == 2
    assert results[0].chunk_id == "docA_c0"
    assert results[0].doc_id == "docA"
    assert results[0].page_number == 1
    assert results[0].score >= 0.99

    # 2. Simulate application restart: instantiate completely new manager pointing to same path
    del manager_session1

    manager_session2 = QdrantStorageManager(storage_path=storage_path)
    # Verify collection exists and documents are still present
    docs = manager_session2.list_documents(collection_name)
    assert len(docs) == 2

    doc_ids = {d["doc_id"] for d in docs}
    assert "docA" in doc_ids
    assert "docB" in doc_ids

    # Verify query works seamlessly after restart
    post_restart_results = manager_session2.search_similar(collection_name, query_vec, top_k=1)
    assert len(post_restart_results) == 1
    assert post_restart_results[0].chunk_id == "docA_c0"

    # Test doc_id filter
    filtered_results = manager_session2.search_similar(
        collection_name,
        query_vec,
        top_k=5,
        doc_id_filter="docB",
    )
    assert len(filtered_results) == 1
    assert filtered_results[0].doc_id == "docB"

    # Test document deletion
    deleted_count = manager_session2.delete_document(collection_name, "docA")
    assert deleted_count == 2

    # After deleting docA, only docB remains
    remaining_docs = manager_session2.list_documents(collection_name)
    assert len(remaining_docs) == 1
    assert remaining_docs[0]["doc_id"] == "docB"
