"""Tests for structured SQL retrieval, SQL safety validation, and NL-to-SQL translation."""

import tempfile
from pathlib import Path
import pytest
from backend.app.database.models import Base, DocumentRecord, DocumentChunkRecord
from backend.app.database.nl_to_sql import NLToSQLTranslator
from backend.app.database.session import get_db_session, init_db, sync_document_deletion, sync_document_ingestion
from backend.app.database.sql_validator import SafeSQLExecutor
from backend.app.schemas.document import DocumentChunk, IngestionResponse


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    init_db(db_path)
    yield db_path

    if db_path.exists():
        db_path.unlink()


def test_sql_validator_allows_valid_selects(temp_db):
    """SafeSQLExecutor must allow valid SELECT queries on allowed tables and columns."""
    executor = SafeSQLExecutor(max_rows=50)

    # Valid queries
    assert executor.validate_query("SELECT doc_id, filename FROM documents")[0] is True
    assert executor.validate_query("SELECT count(*) as total FROM chunks")[0] is True
    assert executor.validate_query("SELECT * FROM documents WHERE file_type = 'pdf'")[0] is True
    assert executor.validate_query("SELECT filename, file_size_bytes FROM documents ORDER BY file_size_bytes DESC LIMIT 5")[0] is True


def test_sql_validator_blocks_destructive_commands(temp_db):
    """SafeSQLExecutor must reject DROP, INSERT, UPDATE, DELETE, ALTER, and PRAGMA."""
    executor = SafeSQLExecutor(max_rows=50)

    for dangerous in [
        "DROP TABLE documents",
        "DELETE FROM chunks",
        "INSERT INTO documents (doc_id, filename) VALUES ('1', 'bad.pdf')",
        "UPDATE documents SET status = 'deleted'",
        "ALTER TABLE documents ADD COLUMN malicious TEXT",
        "PRAGMA table_info(documents)",
    ]:
        is_valid, _, reason = executor.validate_query(dangerous)
        assert is_valid is False, f"Expected {dangerous} to be rejected"
        assert "Prohibited" in reason or "Only SELECT" in reason


def test_sql_validator_blocks_sql_injection_and_multistatements(temp_db):
    """SafeSQLExecutor must reject semicolons, comments, and forbidden tables/columns."""
    executor = SafeSQLExecutor(max_rows=50)

    # Multiple statements
    is_valid, _, reason = executor.validate_query("SELECT * FROM documents; SELECT 1")
    assert is_valid is False
    assert "Multiple statements" in reason

    # Comments
    is_valid, _, reason = executor.validate_query("SELECT * FROM documents -- bypass limit")
    assert is_valid is False
    assert "comment" in reason.lower()

    # Forbidden tables (e.g., sqlite_master)
    is_valid, _, reason = executor.validate_query("SELECT name FROM sqlite_master WHERE type='table'")
    assert is_valid is False
    assert "Access to table" in reason or "disallowed" in reason


def test_nl_to_sql_translation_patterns():
    """NLToSQLTranslator must accurately translate common questions via deterministic rules."""
    translator = NLToSQLTranslator()

    # Total document count
    q1 = "How many documents are uploaded in the system?"
    sql1, method1 = translator.translate(q1)
    assert "SELECT COUNT(*) AS total_documents FROM documents" in sql1
    assert method1 == "rule_pattern"

    # Filter by file type
    q3 = "How many pdf files are uploaded?"
    sql3, method3 = translator.translate(q3)
    assert "WHERE file_type = 'pdf'" in sql3
    assert method3 == "rule_pattern"

    # Largest document
    q4 = "What is the largest document by file size?"
    sql4, method4 = translator.translate(q4)
    assert "ORDER BY file_size_bytes DESC" in sql4
    assert method4 == "rule_pattern"


def test_safe_sql_execution_and_catalog_sync(temp_db):
    """Test full cycle: sync ingested documents to SQLite, translate NL question, execute safe query."""
    executor = SafeSQLExecutor(max_rows=10)
    translator = NLToSQLTranslator()

    # 1. Sync mock document ingestion
    ingest_meta = IngestionResponse(
        doc_id="doc-test-123",
        filename="rag_paper.pdf",
        file_type="pdf",
        file_size_bytes=1048576,
        page_count=12,
        chunk_count=3,
        status="indexed",
        created_at="2026-03-01T00:00:00",
    )
    chunks = [
        DocumentChunk(
            chunk_id=f"chunk-{i}",
            doc_id="doc-test-123",
            filename="rag_paper.pdf",
            text=f"Sample text paragraph {i}",
            page_number=i + 1,
            chunk_index=i,
            token_count_estimate=50,
            char_start=i * 200,
            char_end=(i + 1) * 200,
        )
        for i in range(3)
    ]
    sync_document_ingestion(ingest_meta, chunks)

    # 2. Query document count
    sql, _ = translator.translate("How many documents are uploaded?")
    result = executor.execute(sql)
    assert result["success"] is True
    assert len(result["rows"]) == 1
    assert result["rows"][0]["total_documents"] == "1"

    # 3. Query list of documents
    sql_list, _ = translator.translate("Show all uploaded documents")
    result_list = executor.execute(sql_list)
    assert result_list["success"] is True
    assert len(result_list["rows"]) == 1
    assert result_list["rows"][0]["filename"] == "rag_paper.pdf"
    assert result_list["rows"][0]["file_type"] == "pdf"
    assert result_list["rows"][0]["page_count"] == "12"

    # 4. Test document deletion sync
    deleted_count = sync_document_deletion("doc-test-123")
    assert deleted_count == 1

    # Verify count is now 0
    res_after = executor.execute("SELECT count(*) as total FROM documents")
    assert res_after["rows"][0]["total"] == "0"
