"""Natural Language to Structured SQL translation with strict schema constraints."""

import re
from typing import Optional, Tuple
from backend.app.core.logging import get_logger
from backend.app.database.sql_validator import SafeSQLExecutor
from backend.app.generation.ollama_client import OllamaClient

logger = get_logger(__name__)

SQL_GENERATION_PROMPT = """You are a SQL generator for a structured document catalog database.
Given a user's question, write a single read-only SQLite SELECT query to retrieve the answer.

Database Schema:
- Table `documents`:
  - `id` (INTEGER, PK)
  - `doc_id` (TEXT, UUID)
  - `filename` (TEXT)
  - `file_type` (TEXT: 'pdf', 'docx', 'txt', 'md')
  - `file_size_bytes` (INTEGER)
  - `page_count` (INTEGER)
  - `chunk_count` (INTEGER)
  - `status` (TEXT: 'indexed')
  - `created_at` (DATETIME)
  - `updated_at` (DATETIME)

- Table `chunks`:
  - `id` (INTEGER, PK)
  - `chunk_id` (TEXT)
  - `doc_id` (TEXT, FK to documents.doc_id)
  - `page_number` (INTEGER)
  - `chunk_index` (INTEGER)
  - `token_count_estimate` (INTEGER)

Rules:
1. Return ONLY the raw SQL query. Do not wrap in markdown quotes or add explanations.
2. Use ONLY SELECT statements on `documents` or `chunks`.
3. Never use DROP, INSERT, UPDATE, DELETE, or multiple statements.

Question: {question}

SQL Query:"""


class NLToSQLTranslator:
    """Translates natural language questions about metadata into safe SQL queries."""

    def __init__(self, ollama_client: Optional[OllamaClient] = None, executor: Optional[SafeSQLExecutor] = None):
        self.client = ollama_client
        self.executor = executor or SafeSQLExecutor()

    def translate(self, question: str) -> Tuple[str, str]:
        """Alias for translate_to_sql."""
        return self.translate_to_sql(question)

    def translate_to_sql(self, question: str) -> Tuple[str, str]:
        """Convert question to SQL query. Returns (sql_query, origin_method)."""
        q_lower = question.strip().lower()

        # 1. Fast deterministic rule-based translations for high precision & 0 latency
        # Count queries
        if re.search(r"\b(how many|count|number of)\s+(?:all\s+)?(?:indexed\s+)?(documents|files)\b", q_lower):
            return "SELECT COUNT(*) AS total_documents FROM documents", "rule_pattern"

        if re.search(r"\b(how many|count of|number of)\s+(pdf|docx|txt|md)\b", q_lower):
            match = re.search(r"\b(pdf|docx|txt|md)\b", q_lower)
            ft = match.group(1) if match else "pdf"
            return f"SELECT COUNT(*) AS total_{ft} FROM documents WHERE file_type = '{ft}'", "rule_pattern"

        # List queries
        if re.search(r"\b(list|show|what are)\s+(?:all\s+)?(?:the\s+)?(documents|files|filenames)\b", q_lower):
            return "SELECT filename, file_type, page_count, chunk_count FROM documents ORDER BY created_at DESC", "rule_pattern"

        # Pages / Size queries
        if re.search(r"\b(total|sum of)\s+(pages|page count)\b", q_lower):
            return "SELECT SUM(page_count) AS total_pages FROM documents", "rule_pattern"

        if re.search(r"\b(most pages|largest document|biggest file)\b", q_lower):
            if "page" in q_lower:
                return "SELECT filename, page_count FROM documents ORDER BY page_count DESC LIMIT 1", "rule_pattern"
            return "SELECT filename, file_size_bytes FROM documents ORDER BY file_size_bytes DESC LIMIT 1", "rule_pattern"

        if re.search(r"\b(average|avg)\s+(file size|size)\b", q_lower):
            return "SELECT AVG(file_size_bytes) AS avg_file_size_bytes FROM documents", "rule_pattern"

        if re.search(r"\b(total|sum of)\s+(chunks|chunk count)\b", q_lower):
            return "SELECT SUM(chunk_count) AS total_chunks FROM documents", "rule_pattern"

        # 2. LLM-assisted translation if available
        if self.client:
            try:
                prompt = SQL_GENERATION_PROMPT.format(question=question)
                raw_sql, _, is_fallback = self.client.generate(
                    prompt=prompt,
                    system_prompt="You generate strictly formatted SQLite SELECT queries without explanations.",
                )
                if not is_fallback and raw_sql:
                    cleaned_sql = raw_sql.strip().replace("```sql", "").replace("```", "").strip()
                    is_valid, sanitized, _ = self.executor.validate_query(cleaned_sql)
                    if is_valid:
                        return sanitized, "llm_generated"
            except Exception as e:
                logger.warning(f"LLM SQL generation error: {e}")

        # Default fallback query
        return "SELECT filename, file_type, page_count, chunk_count, created_at FROM documents ORDER BY created_at DESC", "default_fallback"
