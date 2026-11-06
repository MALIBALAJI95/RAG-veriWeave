"""Dependency injection providers for FastAPI endpoints."""

from functools import lru_cache
from backend.app.core.config import Settings, get_settings
from backend.app.embeddings.base import BaseEmbeddings
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
from backend.app.storage.qdrant_client import QdrantStorageManager


# Singleton storage manager
@lru_cache()
def get_storage_manager() -> QdrantStorageManager:
    settings = get_settings()
    manager = QdrantStorageManager(storage_path=settings.QDRANT_STORAGE_PATH)
    manager.ensure_collection(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        vector_size=settings.EMBEDDING_DIMENSION,
    )
    return manager


# Singleton embeddings model
@lru_cache()
def get_embedding_model() -> BaseEmbeddings:
    settings = get_settings()
    return SentenceTransformerEmbeddings(
        model_name=settings.EMBEDDING_MODEL_NAME,
        device=settings.EMBEDDING_DEVICE,
        batch_size=settings.EMBEDDING_BATCH_SIZE,
    )


# Singleton ingestion pipeline
@lru_cache()
def get_ingestion_pipeline() -> IngestionPipeline:
    settings = get_settings()
    storage = get_storage_manager()
    embeddings = get_embedding_model()
    return IngestionPipeline(
        storage_manager=storage,
        embedding_model=embeddings,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        documents_dir=settings.DOCUMENTS_DIR,
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )


# Singleton Ollama client
@lru_cache()
def get_ollama_client() -> OllamaClient:
    settings = get_settings()
    return OllamaClient(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS,
        temperature=settings.OLLAMA_TEMPERATURE,
        enable_fallback=settings.ENABLE_FALLBACK_GENERATOR,
    )


# Singleton baseline dense retriever
@lru_cache()
def get_retriever() -> SimilarityRetriever:
    settings = get_settings()
    storage = get_storage_manager()
    embeddings = get_embedding_model()
    return SimilarityRetriever(
        storage_manager=storage,
        embedding_model=embeddings,
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )


# Singleton BM25 sparse retriever
@lru_cache()
def get_sparse_retriever() -> BM25Retriever:
    settings = get_settings()
    storage = get_storage_manager()
    return BM25Retriever(
        storage_manager=storage,
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )


# Singleton RRF engine
@lru_cache()
def get_rrf_engine() -> RRFFusionEngine:
    settings = get_settings()
    return RRFFusionEngine(k=settings.RRF_K)


# Singleton Cross-Encoder reranker
@lru_cache()
def get_reranker() -> CrossEncoderReranker:
    settings = get_settings()
    return CrossEncoderReranker(
        model_name=settings.RERANKER_MODEL_NAME,
        device=settings.RERANKER_DEVICE,
        enabled=settings.ENABLE_CROSS_ENCODER,
    )


# Singleton Hybrid retriever
@lru_cache()
def get_hybrid_retriever() -> HybridRetriever:
    settings = get_settings()
    dense = get_retriever()
    sparse = get_sparse_retriever()
    return HybridRetriever(
        dense_retriever=dense,
        sparse_retriever=sparse,
        rrf_k=settings.RRF_K,
    )


# Singleton Multi-Query retriever
@lru_cache()
def get_multi_query_retriever() -> MultiQueryRetriever:
    settings = get_settings()
    dense = get_retriever()
    ollama = get_ollama_client()
    return MultiQueryRetriever(
        base_retriever=dense,
        ollama_client=ollama,
        num_queries=settings.MULTI_QUERY_COUNT,
        rrf_k=settings.RRF_K,
    )


# Singleton HyDE retriever
@lru_cache()
def get_hyde_retriever() -> HyDERetriever:
    settings = get_settings()
    storage = get_storage_manager()
    embeddings = get_embedding_model()
    ollama = get_ollama_client()
    return HyDERetriever(
        storage_manager=storage,
        embedding_model=embeddings,
        ollama_client=ollama,
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )


# Singleton Query Decomposition retriever
@lru_cache()
def get_decomposition_retriever() -> QueryDecompositionRetriever:
    settings = get_settings()
    dense = get_retriever()
    ollama = get_ollama_client()
    return QueryDecompositionRetriever(
        base_retriever=dense,
        ollama_client=ollama,
        max_subqueries=settings.DECOMPOSITION_MAX_SUBQUERIES,
        rrf_k=settings.RRF_K,
    )


# Singleton Central Retrieval Orchestrator
@lru_cache()
def get_retrieval_orchestrator() -> RetrievalOrchestrator:
    return RetrievalOrchestrator(
        baseline_retriever=get_retriever(),
        multi_query_retriever=get_multi_query_retriever(),
        hyde_retriever=get_hyde_retriever(),
        decomposition_retriever=get_decomposition_retriever(),
        sparse_retriever=get_sparse_retriever(),
        hybrid_retriever=get_hybrid_retriever(),
        reranker=get_reranker(),
        fusion_engine=get_rrf_engine(),
    )


# Singleton grounded answer generator
@lru_cache()
def get_grounded_generator() -> GroundedAnswerGenerator:
    client = get_ollama_client()
    return GroundedAnswerGenerator(ollama_client=client)
