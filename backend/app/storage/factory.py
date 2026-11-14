"""Storage manager factory for local (Qdrant) vs cloud (Supabase/pgvector) persistence."""

from __future__ import annotations

from typing import Union
from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger
from backend.app.storage.qdrant_client import QdrantStorageManager
from backend.app.storage.supabase_pgvector import SupabasePgVectorStorageManager

logger = get_logger(__name__)

StorageManagerType = Union[QdrantStorageManager, SupabasePgVectorStorageManager]


def create_storage_manager(settings: Settings | None = None) -> StorageManagerType:
    """Instantiate appropriate storage manager based on runtime configuration."""
    if settings is None:
        settings = get_settings()

    backend = (settings.VECTOR_STORAGE_BACKEND or "qdrant").lower()
    resolved_db_url = settings.resolved_database_url

    # Cloud pgvector requested explicitly or auto-detected when database URL is Postgres and pgvector requested
    if backend in ("pgvector", "supabase") or (backend == "auto" and resolved_db_url):
        if not resolved_db_url:
            logger.warning(
                "pgvector backend was requested but no DATABASE_URL or SUPABASE_DB_URL is set! "
                "Falling back to local Qdrant."
            )
            return QdrantStorageManager(storage_path=settings.QDRANT_STORAGE_PATH)

        logger.info(f"Using cloud Supabase / pgvector storage manager.")
        return SupabasePgVectorStorageManager(database_url=resolved_db_url)

    # Default to local Qdrant storage
    logger.debug(f"Using persistent on-disk Qdrant storage manager at: {settings.QDRANT_STORAGE_PATH}")
    return QdrantStorageManager(storage_path=settings.QDRANT_STORAGE_PATH)
