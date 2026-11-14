"""SQLite session management and schema synchronization."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Generator, List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from backend.app.core.logging import get_logger
from backend.app.database.models import Base, DocumentChunkRecord, DocumentRecord

if TYPE_CHECKING:
    from backend.app.schemas.document import DocumentChunk, IngestionResponse

logger = get_logger(__name__)

_engine = None
_SessionFactory = None


def init_db(
    db_path: Optional[Path] = None,
    database_url: Optional[str] = None,
) -> sessionmaker:
    """Initialize database engine (PostgreSQL if URL provided, else SQLite) and ensure tables exist."""
    global _engine, _SessionFactory
    
    if database_url:
        logger.info(f"Initializing cloud PostgreSQL database session: {database_url.split('@')[-1] if '@' in database_url else 'configured'}")
        _engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
        )
    else:
        target_path = db_path or Path("./data/veriweave.db")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        sqlite_url = f"sqlite:///{target_path.resolve()}"
        logger.info(f"Initializing SQLite structured database at: {sqlite_url}")
        _engine = create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )

    Base.metadata.create_all(bind=_engine)
    _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _SessionFactory


def reset_engine() -> None:
    """Reset the global database engine and session factory."""
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionFactory = None


def get_session_factory() -> sessionmaker:
    """Return configured session factory or initialize with default settings."""
    global _SessionFactory
    if _SessionFactory is None:
        from backend.app.core.config import get_settings
        settings = get_settings()
        if settings.resolved_database_url:
            _SessionFactory = init_db(database_url=settings.resolved_database_url)
        else:
            _SessionFactory = init_db(db_path=settings.SQLITE_DB_PATH)
    return _SessionFactory


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session scope."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def sync_document_ingestion(
    ingestion: IngestionResponse,
    chunks: Optional[List[DocumentChunk]] = None,
) -> None:
    """Synchronize document ingestion results into structured SQLite database."""
    try:
        with get_db_session() as session:
            # Check if record already exists
            existing = session.query(DocumentRecord).filter(DocumentRecord.doc_id == ingestion.doc_id).first()
            if existing:
                existing.filename = ingestion.filename
                existing.file_type = ingestion.file_type
                existing.file_size_bytes = ingestion.file_size_bytes
                existing.page_count = ingestion.page_count
                existing.chunk_count = ingestion.chunk_count
                existing.status = ingestion.status
                existing.updated_at = datetime.utcnow()
                # Remove old chunks
                session.query(DocumentChunkRecord).filter(DocumentChunkRecord.doc_id == ingestion.doc_id).delete()
            else:
                doc = DocumentRecord(
                    doc_id=ingestion.doc_id,
                    filename=ingestion.filename,
                    file_type=ingestion.file_type,
                    file_size_bytes=ingestion.file_size_bytes,
                    page_count=ingestion.page_count,
                    chunk_count=ingestion.chunk_count,
                    status=ingestion.status,
                )
                session.add(doc)

            # Insert chunk records
            if chunks:
                chunk_records = [
                    DocumentChunkRecord(
                        chunk_id=c.chunk_id,
                        doc_id=c.doc_id,
                        page_number=c.page_number,
                        chunk_index=c.chunk_index,
                        token_count_estimate=c.token_count_estimate,
                        char_start=c.char_start,
                        char_end=c.char_end,
                    )
                    for c in chunks
                ]
                session.add_all(chunk_records)

        logger.info(f"Synchronized document metadata into SQLite for '{ingestion.filename}' (doc_id={ingestion.doc_id})")
    except Exception as e:
        logger.warning(f"Could not synchronize document metadata to SQLite: {e}")


def sync_document_deletion(doc_id: str) -> int:
    """Delete document and related chunks from structured SQLite database."""
    try:
        with get_db_session() as session:
            count = session.query(DocumentRecord).filter(DocumentRecord.doc_id == doc_id).delete()
            logger.info(f"Deleted SQLite document record for doc_id='{doc_id}' (count={count})")
            return count
    except Exception as e:
        logger.warning(f"Could not delete document from SQLite: {e}")
        return 0
