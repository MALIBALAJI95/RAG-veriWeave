"""SQL validation and safe parameterized execution engine."""

import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import text
from backend.app.core.logging import get_logger
from backend.app.database.session import get_db_session

logger = get_logger(__name__)

# Strict Security Allowlist
ALLOWED_TABLES: Set[str] = {"documents", "chunks"}

ALLOWED_COLUMNS: Dict[str, Set[str]] = {
    "documents": {
        "id",
        "doc_id",
        "filename",
        "file_type",
        "file_size_bytes",
        "page_count",
        "chunk_count",
        "status",
        "created_at",
        "updated_at",
    },
    "chunks": {
        "id",
        "chunk_id",
        "doc_id",
        "page_number",
        "chunk_index",
        "token_count_estimate",
        "char_start",
        "char_end",
    },
}

# Strictly prohibited patterns
DESTRUCTIVE_PATTERN = re.compile(
    r"\b(DROP|ALTER|INSERT|UPDATE|DELETE|TRUNCATE|EXEC|EXECUTE|CREATE|ATTACH|DETACH|PRAGMA|REINDEX|VACUUM|RENAME|GRANT|REVOKE)\b",
    re.IGNORECASE,
)
MULTIPLE_STATEMENT_PATTERN = re.compile(r";(?!\s*$)")
COMMENT_PATTERN = re.compile(r"(--|/\*|\*/)")


class SQLSecurityError(Exception):
    """Raised when an SQL query violates security or schema allowlists."""
    pass


class SafeSQLExecutor:
    """Validates and executes read-only SELECT queries with schema allowlists and row limits."""

    def __init__(self, max_rows: int = 50, timeout_seconds: float = 5.0):
        self.max_rows = max_rows
        self.timeout_seconds = timeout_seconds

    def validate_query(self, query: str) -> Tuple[bool, str, str]:
        """Validate query syntax, operations, tables, and safety.

        Returns: (is_valid, sanitized_query_or_empty, reason)
        """
        cleaned = query.strip()
        if not cleaned:
            return False, "", "Empty query string."

        # 1. Enforce SELECT only
        if not re.match(r"^SELECT\b", cleaned, re.IGNORECASE):
            return False, "", "Only SELECT operations are permitted."

        # 2. Block destructive commands
        if DESTRUCTIVE_PATTERN.search(cleaned):
            match = DESTRUCTIVE_PATTERN.search(cleaned).group(0)
            return False, "", f"Prohibited SQL keyword detected: '{match}'"

        # 3. Block multiple statements (semicolon injection)
        if MULTIPLE_STATEMENT_PATTERN.search(cleaned):
            return False, "", "Multiple statements or chained SQL queries are prohibited."

        # 4. Block SQL comments to prevent parser tampering
        if COMMENT_PATTERN.search(cleaned):
            return False, "", "SQL comment characters ('--', '/*') are prohibited."

        # Strip trailing semicolon if present
        sanitized = re.sub(r";\s*$", "", cleaned)

        # 5. Extract referenced tables and verify against allowlist
        # Match FROM <table> and JOIN <table>
        table_matches = re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", sanitized, re.IGNORECASE)
        for tbl in table_matches:
            tbl_clean = tbl.lower().strip()
            if tbl_clean not in ALLOWED_TABLES:
                return False, "", f"Access to table '{tbl_clean}' is not permitted. Allowed tables: {sorted(ALLOWED_TABLES)}"

        # 6. Enforce safe LIMIT
        limit_match = re.search(r"\bLIMIT\s+(\d+)", sanitized, re.IGNORECASE)
        if limit_match:
            requested_limit = int(limit_match.group(1))
            if requested_limit > self.max_rows:
                # Clamp to max_rows
                sanitized = re.sub(r"\bLIMIT\s+\d+", f"LIMIT {self.max_rows}", sanitized, flags=re.IGNORECASE)
        else:
            sanitized = f"{sanitized} LIMIT {self.max_rows}"

        return True, sanitized, "Query validated successfully."

    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a validated query within a read-only transaction and return structured results."""
        start_time = time.perf_counter()
        params = params or {}

        # Validate query
        is_valid, safe_sql, reason = self.validate_query(query)
        if not is_valid:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(f"SQL Validation Rejected: {reason} | Raw Query: '{query}'")
            return {
                "success": False,
                "error": reason,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "query_executed": query,
                "latency_ms": round(elapsed_ms, 2),
            }

        try:
            with get_db_session() as session:
                cursor = session.execute(text(safe_sql), params)
                columns = list(cursor.keys())
                raw_rows = cursor.fetchall()
                # Convert rows to dicts
                rows = [dict(zip(columns, [str(v) if v is not None else None for v in row])) for row in raw_rows]

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"Safe SQL executed in {elapsed_ms:.2f}ms -> {len(rows)} rows: '{safe_sql}'")
            return {
                "success": True,
                "error": None,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "query_executed": safe_sql,
                "latency_ms": round(elapsed_ms, 2),
            }
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"SQL execution error on '{safe_sql}': {e}")
            return {
                "success": False,
                "error": f"Database execution error: {str(e)}",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "query_executed": safe_sql,
                "latency_ms": round(elapsed_ms, 2),
            }
