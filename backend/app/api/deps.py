"""Dependency injection providers for FastAPI endpoints."""

from functools import lru_cache
from typing import Generator
from backend.app.core.config import Settings, get_settings
from backend.app.embeddings.base import BaseEmbeddings
from backend.app.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from backend.app.generation.grounded_generator import GroundedAnswerGenerator
from backend.app.generation.ollama_client import OllamaClient
from backend.app.ingestion.pipeline import IngestionPipeline
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


# Singleton retriever
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


# Singleton grounded answer generator
@lru_cache()
def get_grounded_generator() -> GroundedAnswerGenerator:
    client = get_ollama_client()
    return GroundedAnswerGenerator(ollama_client=client)
