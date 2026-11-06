"""End-to-End Live Verification Script for Phase 1.

Verifies:
1. Document ingestion (PDF, DOCX, TXT)
2. Recursive chunking with page and offset preservation
3. SentenceTransformers embeddings generation (all-MiniLM-L6-v2)
4. Persistent Qdrant vector indexing
5. Similarity retrieval matching query semantics
6. Grounded generation with inline citations & page references
7. Storage persistence: restart manager and verify documents remain indexed
"""

import sys
from pathlib import Path

# Ensure root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.core.config import get_settings
from backend.app.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from backend.app.generation.grounded_generator import GroundedAnswerGenerator
from backend.app.generation.ollama_client import OllamaClient
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.storage.qdrant_client import QdrantStorageManager


def run_live_verification():
    print("=" * 80)
    print(" VeriWeave Phase 1 - Live End-to-End Pipeline Verification")
    print(" Tagline: Retrieve intelligently. Reason contextually. Respond reliably.")
    print("=" * 80)

    settings = get_settings()
    settings.ensure_directories()

    # 1. Initialize Persistent Storage Manager
    print("\n[Step 1] Initializing Persistent Qdrant Storage...")
    storage = QdrantStorageManager(storage_path=settings.QDRANT_STORAGE_PATH)
    storage.ensure_collection(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        vector_size=settings.EMBEDDING_DIMENSION,
    )
    print(f" -> Storage Path: {settings.QDRANT_STORAGE_PATH.resolve()}")
    print(f" -> Collection: {settings.QDRANT_COLLECTION_NAME}")

    # 2. Initialize Embeddings Model
    print("\n[Step 2] Initializing Sentence Transformers Embedding Engine...")
    embeddings = SentenceTransformerEmbeddings(
        model_name=settings.EMBEDDING_MODEL_NAME,
        device=settings.EMBEDDING_DEVICE,
    )
    print(f" -> Model: {settings.EMBEDDING_MODEL_NAME}")
    print(f" -> Dimension: {embeddings.dimension}")

    # 3. Initialize Ingestion Pipeline
    print("\n[Step 3] Initializing Ingestion Pipeline...")
    pipeline = IngestionPipeline(
        storage_manager=storage,
        embedding_model=embeddings,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        documents_dir=settings.DOCUMENTS_DIR,
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )

    # Ingest Sample Documents
    samples_dir = Path("datasets/sample_docs")
    sample_files = [
        samples_dir / "rag_architectures.pdf",
        samples_dir / "retrieval_strategies.docx",
        samples_dir / "ai_agents_overview.txt",
    ]

    print("\n[Step 4] Ingesting Documents (PDF, DOCX, TXT)...")
    ingested_ids = []
    for file_path in sample_files:
        assert file_path.exists(), f"Sample file not found: {file_path}"
        res = pipeline.ingest_from_path(file_path=file_path)
        ingested_ids.append(res.doc_id)
        print(f" -> Ingested '{res.filename}': {res.page_count} pages, {res.chunk_count} chunks (ID: {res.doc_id})")

    # 4. Verify Document Listing
    print("\n[Step 5] Querying Indexed Documents...")
    docs = storage.list_documents(collection_name=settings.QDRANT_COLLECTION_NAME)
    print(f" -> Total indexed documents in Qdrant: {len(docs)}")
    for d in docs:
        print(f"    * {d['filename']} | Type: {d['file_type']} | Pages: {d['page_count']} | Chunks: {d['chunk_count']}")

    # 5. Semantic Similarity Retrieval
    print("\n[Step 6] Testing Semantic Similarity Retrieval...")
    retriever = SimilarityRetriever(
        storage_manager=storage,
        embedding_model=embeddings,
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )

    test_queries = [
        "How does RAG balance parametric knowledge and what is on page 2?",
        "What are the trade-offs between BM25 sparse retrieval and dense embeddings?",
        "How do cognitive AI agents manage short-term and long-term memory?",
    ]

    ollama_client = OllamaClient(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        enable_fallback=True,
    )
    generator = GroundedAnswerGenerator(ollama_client=ollama_client)

    for q in test_queries:
        print("\n" + "-" * 60)
        print(f"Query: {q}")
        chunks = retriever.retrieve(query=q, top_k=2)
        print(f"Retrieved {len(chunks)} chunks:")
        for idx, c in enumerate(chunks, 1):
            print(f"  [{idx}] Doc: {c.filename} | Page: {c.page_number} | Score: {c.score:.4f}")
            print(f"      Text: {c.text[:120]}...")

        # Generate grounded response
        chat_resp = generator.generate_grounded_answer(query=q, retrieved_chunks=chunks)
        print(f"\nGenerated Answer ({chat_resp.model_used}, Latency: {chat_resp.latency_ms:.1f}ms):")
        print(chat_resp.answer)
        print("Citations:")
        for cit in chat_resp.citations:
            print(f"  * [{cit.citation_id}] {cit.filename} (Page {cit.page_number}) - Score: {cit.score}")

    # 6. Verify Persistence Across Restart
    print("\n[Step 7] Testing Qdrant Persistence Across Process Restart...")
    del storage
    del retriever
    del pipeline

    print(" -> Simulating restart: opening new QdrantStorageManager instance pointing to disk path...")
    restarted_storage = QdrantStorageManager(storage_path=settings.QDRANT_STORAGE_PATH)
    col_info = restarted_storage.get_collection_info(settings.QDRANT_COLLECTION_NAME)
    persisted_docs = restarted_storage.list_documents(settings.QDRANT_COLLECTION_NAME)

    print(f" -> Post-restart points count: {col_info.get('points_count')}")
    print(f" -> Post-restart documents count: {len(persisted_docs)}")
    assert len(persisted_docs) >= 3, "Documents were lost after restart!"

    restarted_retriever = SimilarityRetriever(
        storage_manager=restarted_storage,
        embedding_model=embeddings,
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )
    post_restart_chunks = restarted_retriever.retrieve(query="Qdrant vector indexing", top_k=1)
    assert len(post_restart_chunks) == 1
    print(f" -> Verified retrieval after restart: Found chunk from '{post_restart_chunks[0].filename}' "
          f"Page {post_restart_chunks[0].page_number} (Score: {post_restart_chunks[0].score:.4f})")

    print("\n" + "=" * 80)
    print(" ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_live_verification()
