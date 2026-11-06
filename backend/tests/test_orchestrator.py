"""Unit tests for central Retrieval Orchestrator."""

from backend.app.embeddings.base import BaseEmbeddings
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
from backend.app.schemas.chat import RetrievalStrategy
from backend.app.storage.qdrant_client import QdrantStorageManager


def test_orchestrator_all_strategies(
    test_pipeline: IngestionPipeline,
    test_storage: QdrantStorageManager,
    mock_embeddings: BaseEmbeddings,
    sample_txt_path,
):
    test_pipeline.ingest_from_path(sample_txt_path, doc_id="orch_doc")

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

    rrf = RRFFusionEngine(k=60)
    ollama = OllamaClient(base_url="http://localhost:99999", enable_fallback=True)

    hybrid = HybridRetriever(dense, sparse, rrf_k=60)
    mq = MultiQueryRetriever(dense, ollama, num_queries=2, rrf_k=60)
    hyde = HyDERetriever(test_storage, mock_embeddings, ollama, collection_name="test_collection")
    decomp = QueryDecompositionRetriever(dense, ollama, max_subqueries=2, rrf_k=60)
    reranker = CrossEncoderReranker(enabled=False)

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

    query = "Autonomous agents architecture and memory"

    strategies_to_test = [
        RetrievalStrategy.BASELINE,
        RetrievalStrategy.MULTI_QUERY,
        RetrievalStrategy.HYDE,
        RetrievalStrategy.DECOMPOSITION,
        RetrievalStrategy.FUSION,
        RetrievalStrategy.HYBRID,
        RetrievalStrategy.HYBRID_RERANK,
        RetrievalStrategy.RERANK,
    ]

    for strat in strategies_to_test:
        chunks, meta = orchestrator.retrieve(query=query, strategy=strat, top_k=2)
        assert len(chunks) > 0, f"Strategy {strat} returned empty chunks"
        assert meta.strategy == strat
        assert meta.retrieval_latency_ms >= 0.0
        assert meta.returned_candidate_count == len(chunks)
