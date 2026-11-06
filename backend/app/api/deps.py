"""Dependency injection providers for FastAPI endpoints."""

from functools import lru_cache
from backend.app.core.config import Settings, get_settings
from backend.app.database.session import init_db
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
from backend.app.routing.classifier import RouteClassifier
from backend.app.routing.handlers.sql_handler import SQLRouteHandler
from backend.app.routing.handlers.vector_handler import VectorRouteHandler
from backend.app.routing.handlers.web_handler import WebRouteHandler
from backend.app.routing.orchestrator import RoutingOrchestrator
from backend.app.storage.qdrant_client import QdrantStorageManager
from backend.app.web_search.factory import get_web_search_provider


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
    # Ensure SQLite DB is initialized
    init_db(settings.SQLITE_DB_PATH)
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


# Singleton Route Classifier
@lru_cache()
def get_route_classifier() -> RouteClassifier:
    settings = get_settings()
    ollama = get_ollama_client()
    return RouteClassifier(
        ollama_client=ollama,
        confidence_threshold=settings.ROUTING_CONFIDENCE_THRESHOLD,
    )


# Singleton Vector Route Handler
@lru_cache()
def get_vector_route_handler() -> VectorRouteHandler:
    return VectorRouteHandler(orchestrator=get_retrieval_orchestrator())


# Singleton SQL Route Handler
@lru_cache()
def get_sql_route_handler() -> SQLRouteHandler:
    settings = get_settings()
    ollama = get_ollama_client()
    init_db(settings.SQLITE_DB_PATH)
    return SQLRouteHandler(
        ollama_client=ollama,
        max_rows=settings.SQL_MAX_ROWS,
        timeout_seconds=settings.SQL_EXECUTION_TIMEOUT_SECONDS,
    )


# Singleton Web Route Handler
@lru_cache()
def get_web_route_handler() -> WebRouteHandler:
    settings = get_settings()
    provider = get_web_search_provider()
    return WebRouteHandler(provider=provider, max_results=settings.WEB_SEARCH_MAX_RESULTS)


# Singleton Intelligent Routing Orchestrator
@lru_cache()
def get_routing_orchestrator() -> RoutingOrchestrator:
    return RoutingOrchestrator(
        classifier=get_route_classifier(),
        vector_handler=get_vector_route_handler(),
        sql_handler=get_sql_route_handler(),
        web_handler=get_web_route_handler(),
    )


# Singleton grounded answer generator
@lru_cache()
def get_grounded_generator() -> GroundedAnswerGenerator:
    client = get_ollama_client()
    return GroundedAnswerGenerator(ollama_client=client)
