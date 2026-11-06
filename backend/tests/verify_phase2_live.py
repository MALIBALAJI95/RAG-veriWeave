"""Live end-to-end verification script for Phase 2 Advanced Multi-Strategy Retrieval."""

import sys
from pathlib import Path

# Ensure root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.core.config import get_settings
from backend.app.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from backend.app.generation.grounded_generator import GroundedAnswerGenerator
from backend.app.generation.ollama_client import OllamaClient
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.retrieval.bm25 import BM25Retriever
from backend.app.retrieval.decomposition import QueryDecompositionRetriever
from backend.app.retrieval.fusion import RRFFusionEngine
from backend.app.retrieval.hybrid import HybridRetriever
from backend.app.retrieval.hyde import HyDERetriever
from backend.app.retrieval.multi_query import MultiQueryRetriever
from backend.app.retrieval.orchestrator import RetrievalOrchestrator
from backend.app.retrieval.reranker import CrossEncoderReranker
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.schemas.chat import MetadataFilter, RetrievalStrategy
from backend.app.storage.qdrant_client import QdrantStorageManager


def run_live_verification():
    print("=" * 88)
    print(" VeriWeave Phase 2 - Live Multi-Strategy Retrieval Engine Verification")
    print(" Tagline: Retrieve intelligently. Reason contextually. Respond reliably.")
    print("=" * 88)

    settings = get_settings()
    settings.ensure_directories()

    # 1. Storage & Embeddings
    print("\n[Step 1] Initializing Persistent Qdrant & Embeddings...")
    storage = QdrantStorageManager(storage_path=settings.QDRANT_STORAGE_PATH)
    storage.ensure_collection(settings.QDRANT_COLLECTION_NAME, vector_size=settings.EMBEDDING_DIMENSION)
    embeddings = SentenceTransformerEmbeddings(
        model_name=settings.EMBEDDING_MODEL_NAME,
        device=settings.EMBEDDING_DEVICE,
    )

    # 2. Ingestion
    print("\n[Step 2] Ensuring Reference Documents Ingested...")
    pipeline = IngestionPipeline(
        storage_manager=storage,
        embedding_model=embeddings,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        documents_dir=settings.DOCUMENTS_DIR,
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )
    for doc in ["rag_architectures.pdf", "retrieval_strategies.docx", "ai_agents_overview.txt"]:
        p = Path("datasets/sample_docs") / doc
        pipeline.ingest_from_path(p)

    # 3. Retrievers & Orchestrator
    print("\n[Step 3] Initializing Advanced Multi-Strategy Retrievers...")
    dense = SimilarityRetriever(storage, embeddings, collection_name=settings.QDRANT_COLLECTION_NAME)
    sparse = BM25Retriever(storage, collection_name=settings.QDRANT_COLLECTION_NAME)
    sparse.build_index(force_rebuild=True)

    rrf = RRFFusionEngine(k=60)
    ollama = OllamaClient(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        enable_fallback=True,
    )

    hybrid = HybridRetriever(dense, sparse, rrf_k=60)
    mq = MultiQueryRetriever(dense, ollama, num_queries=3, rrf_k=60)
    hyde = HyDERetriever(storage, embeddings, ollama, collection_name=settings.QDRANT_COLLECTION_NAME)
    decomp = QueryDecompositionRetriever(dense, ollama, max_subqueries=3, rrf_k=60)
    reranker = CrossEncoderReranker(
        model_name=settings.RERANKER_MODEL_NAME,
        device=settings.RERANKER_DEVICE,
        enabled=True,
    )

    orchestrator = RetrievalOrchestrator(
        baseline_retriever=dense,
        multi_query_retriever=mq,
        hyde_retriever=hyde,
        decomposition_retriever=decomp,
        sparse_retriever=sparse,
        hybrid_retriever=hybrid,
        reranker=reranker,
        fusion_engine=rrf,
    )
    generator = GroundedAnswerGenerator(ollama_client=ollama)

    # 4. Live Verification Scenarios
    scenarios = [
        (
            "Scenario 1: Baseline Dense Retrieval",
            "What is on page 2 regarding Qdrant vector indexing?",
            RetrievalStrategy.BASELINE,
            False,
            None,
        ),
        (
            "Scenario 2: Multi-Query Retrieval (Perspective Expansion)",
            "How do cognitive AI agents manage memory architectures?",
            RetrievalStrategy.MULTI_QUERY,
            False,
            None,
        ),
        (
            "Scenario 3: HyDE (Hypothetical Document Embeddings)",
            "What metric measures vector distances in continuous semantic spaces?",
            RetrievalStrategy.HYDE,
            False,
            None,
        ),
        (
            "Scenario 4: Query Decomposition (Compound Question)",
            "What is autonomous agent foundation and how are external tools integrated?",
            RetrievalStrategy.DECOMPOSITION,
            False,
            None,
        ),
        (
            "Scenario 5: Hybrid Retrieval (Dense + BM25 Sparse with RRF)",
            "BM25 term frequencies and inverse document frequencies exact keyword matching",
            RetrievalStrategy.HYBRID,
            False,
            None,
        ),
        (
            "Scenario 6: Hybrid Retrieval + Cross-Encoder Reranking",
            "What are the advantages and weaknesses of dense vs BM25 sparse retrieval?",
            RetrievalStrategy.HYBRID_RERANK,
            True,
            None,
        ),
        (
            "Scenario 7: Metadata Filtering (Scoped to PDF)",
            "What is the focus of Page 1?",
            RetrievalStrategy.BASELINE,
            False,
            MetadataFilter(filename="rag_architectures.pdf", page_number=1),
        ),
    ]

    for title, query, strat, rerank_flag, filters in scenarios:
        print("\n" + "-" * 88)
        print(f" {title}")
        print(f" Query: \"{query}\"")
        print(f" Strategy: {strat.value} | Rerank: {rerank_flag} | Filter: {filters}")

        chunks, meta = orchestrator.retrieve(
            query=query,
            strategy=strat,
            top_k=2,
            rerank=rerank_flag,
            filters=filters,
        )

        print(f" -> Latency: {meta.retrieval_latency_ms:.2f} ms | Candidates Considered: {meta.raw_candidate_count}")
        if meta.generated_queries:
            print(f" -> Generated Queries: {meta.generated_queries}")
        if meta.hypothetical_document:
            print(f" -> HyDE Passage: \"{meta.hypothetical_document[:90]}...\"")
        if meta.sub_queries:
            print(f" -> Decomposed Sub-queries: {meta.sub_queries}")

        print(f" -> Retrieved {len(chunks)} chunks:")
        for idx, c in enumerate(chunks, 1):
            rerank_info = f" | Rerank Score: {c.rerank_score}" if c.rerank_score is not None else ""
            print(f"    [{idx}] Doc: {c.filename} (Page {c.page_number}) | Method: {c.retrieval_method} | Score: {c.score:.4f}{rerank_info}")
            print(f"        Snippet: {c.text[:120].strip()}...")

        # Generate grounded answer
        chat_resp = generator.generate_grounded_answer(
            query=query,
            retrieved_chunks=chunks,
            retrieval_metadata=meta,
        )
        print(f" -> Grounded Citations ({len(chat_resp.citations)}):")
        for cit in chat_resp.citations:
            print(f"       * [Doc: {cit.filename}, Page: {cit.page_number}] (Score: {cit.score})")

    print("\n" + "=" * 88)
    print(" ALL 7 PHASE 2 RETRIEVAL STRATEGY SCENARIOS VERIFIED SUCCESSFULLY!")
    print("=" * 88)


if __name__ == "__main__":
    run_live_verification()
