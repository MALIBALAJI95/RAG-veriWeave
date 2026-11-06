"""Database package exports."""

from backend.app.database.models import Base, DocumentChunkRecord, DocumentRecord
from backend.app.database.nl_to_sql import NLToSQLTranslator
from backend.app.database.session import (
    get_db_session,
    get_session_factory,
    init_db,
    sync_document_deletion,
    sync_document_ingestion,
)
from backend.app.database.sql_validator import (
    ALLOWED_COLUMNS,
    ALLOWED_TABLES,
    SafeSQLExecutor,
    SQLSecurityError,
)

__all__ = [
    "Base",
    "DocumentRecord",
    "DocumentChunkRecord",
    "init_db",
    "get_db_session",
    "get_session_factory",
    "sync_document_ingestion",
    "sync_document_deletion",
    "ALLOWED_TABLES",
    "ALLOWED_COLUMNS",
    "SafeSQLExecutor",
    "SQLSecurityError",
    "NLToSQLTranslator",
]
