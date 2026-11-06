"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "VeriWeave"
    APP_TAGLINE: str = "Retrieve intelligently. Reason contextually. Respond reliably."
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Storage Paths (resolved relative to repository root or absolute)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = Field(default_factory=lambda: Path("./data"))
    DOCUMENTS_DIR: Path = Field(default_factory=lambda: Path("./data/documents"))
    QDRANT_STORAGE_PATH: Path = Field(default_factory=lambda: Path("./data/qdrant_storage"))
    QDRANT_COLLECTION_NAME: str = "veriweave_documents"
    SQLITE_DB_PATH: Path = Field(default_factory=lambda: Path("./data/veriweave.db"))

    # Phase 3: Intelligent Query Routing & Multi-Source Configuration
    DEFAULT_ROUTING_MODE: str = "auto"
    ROUTING_CONFIDENCE_THRESHOLD: float = 0.65
    ENABLE_SQL_ROUTING: bool = True
    SQL_MAX_ROWS: int = 50
    SQL_EXECUTION_TIMEOUT_SECONDS: float = 5.0
    ENABLE_WEB_SEARCH: bool = True
    WEB_SEARCH_PROVIDER: str = "mock"
    WEB_SEARCH_MAX_RESULTS: int = 3

    # Embeddings Configuration
    # sentence-transformers/all-MiniLM-L6-v2 is ultra-lightweight (80MB, 384-dim, fast on Apple Silicon M-series)
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_DIMENSION: int = 384

    # Ingestion & Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100

    # Phase 2: Advanced Retrieval Configuration
    DEFAULT_RETRIEVAL_STRATEGY: str = "baseline"
    RRF_K: int = 60
    MULTI_QUERY_COUNT: int = 3
    DECOMPOSITION_MAX_SUBQUERIES: int = 3
    HYBRID_DENSE_WEIGHT: float = 0.5
    HYBRID_SPARSE_WEIGHT: float = 0.5
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANKER_DEVICE: str = "cpu"
    RERANK_TOP_N: int = 10
    ENABLE_CROSS_ENCODER: bool = True

    # Ollama LLM Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0
    OLLAMA_TEMPERATURE: float = 0.1

    # Fallback Generator: active when Ollama is unreachable, returns structured grounded response
    ENABLE_FALLBACK_GENERATOR: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"

    def ensure_directories(self) -> None:
        """Ensure runtime directories exist on the filesystem."""
        for path in [self.DATA_DIR, self.DOCUMENTS_DIR, self.QDRANT_STORAGE_PATH]:
            path.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
