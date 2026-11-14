"""Supabase and PostgreSQL pgvector storage manager for cloud persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from backend.app.core.exceptions import VectorStorageError
from backend.app.core.logging import get_logger
from backend.app.schemas.chat import RetrievedChunk
from backend.app.schemas.document import DocumentChunk

logger = get_logger(__name__)


class SupabasePgVectorStorageManager:
    """Manages cloud-hosted PostgreSQL vector storage with pgvector extension."""

    def __init__(self, database_url: str):
        if not database_url:
            raise VectorStorageError("PostgreSQL database URL is required for SupabasePgVectorStorageManager")

        # Normalize URL scheme for SQLAlchemy (postgres:// -> postgresql://)
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        self.database_url = database_url
        self.engine: Engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        logger.info(
            "Initialized SupabasePgVectorStorageManager with host: "
            f"{database_url.split('@')[-1] if '@' in database_url else 'configured'}"
        )

    def ensure_collection(
        self,
        collection_name: str = "veriweave_vectors",
        vector_size: int = 384,
        distance: Any = None,
    ) -> None:
        """Ensure pgvector extension is enabled and vector table with indexes exists."""
        try:
            with self.engine.begin() as conn:
                # 1. Enable pgvector extension
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                except Exception as ext_err:
                    logger.warning(f"Could not execute CREATE EXTENSION vector (may already exist or insufficient permissions): {ext_err}")

                # 2. Create vectors table
                create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {collection_name} (
                    id SERIAL PRIMARY KEY,
                    chunk_id VARCHAR(128) UNIQUE NOT NULL,
                    doc_id VARCHAR(64) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    page_number INTEGER NOT NULL DEFAULT 1,
                    chunk_index INTEGER NOT NULL DEFAULT 0,
                    text TEXT NOT NULL,
                    char_start INTEGER DEFAULT 0,
                    char_end INTEGER DEFAULT 0,
                    token_count_estimate INTEGER DEFAULT 0,
                    metadata JSONB DEFAULT '{{}}'::jsonb,
                    embedding vector({vector_size}),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
                conn.execute(text(create_table_sql))

                # 3. Create indexes for performance
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{collection_name}_doc_id ON {collection_name} (doc_id);"))
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{collection_name}_filename ON {collection_name} (filename);"))

                # 4. Create HNSW vector index if not exists (fallback to IVFFlat or none if index creation fails)
                try:
                    conn.execute(text(
                        f"CREATE INDEX IF NOT EXISTS idx_{collection_name}_vector_hnsw "
                        f"ON {collection_name} USING hnsw (embedding vector_cosine_ops);"
                    ))
                except Exception as hnsw_err:
                    logger.warning(f"HNSW index could not be created directly (will use sequential/table scan): {hnsw_err}")

            logger.info(f"Verified Supabase pgvector table '{collection_name}' (dim={vector_size})")
        except Exception as e:
            logger.error(f"Failed to ensure pgvector collection '{collection_name}': {e}")
            raise VectorStorageError(f"Failed to initialize pgvector table {collection_name}: {str(e)}")

    def upsert_chunks(
        self,
        collection_name: str,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> int:
        """Upsert document chunks and their vector embeddings into pgvector."""
        if not chunks:
            return 0
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunk count ({len(chunks)}) does not match embedding count ({len(embeddings)})")

        upsert_sql = text(f"""
            INSERT INTO {collection_name} (
                chunk_id, doc_id, filename, page_number, chunk_index,
                text, char_start, char_end, token_count_estimate, metadata, embedding
            )
            VALUES (
                :chunk_id, :doc_id, :filename, :page_number, :chunk_index,
                :text, :char_start, :char_end, :token_count_estimate, :metadata::jsonb, :embedding
            )
            ON CONFLICT (chunk_id) DO UPDATE SET
                doc_id = EXCLUDED.doc_id,
                filename = EXCLUDED.filename,
                page_number = EXCLUDED.page_number,
                chunk_index = EXCLUDED.chunk_index,
                text = EXCLUDED.text,
                char_start = EXCLUDED.char_start,
                char_end = EXCLUDED.char_end,
                token_count_estimate = EXCLUDED.token_count_estimate,
                metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding;
        """)

        try:
            with self.engine.begin() as conn:
                for chunk, emb in zip(chunks, embeddings):
                    # pgvector expects string representation like '[0.1, 0.2, ...]'
                    emb_str = f"[{','.join(str(float(x)) for x in emb)}]"
                    conn.execute(
                        upsert_sql,
                        {
                            "chunk_id": chunk.chunk_id,
                            "doc_id": chunk.doc_id,
                            "filename": chunk.filename,
                            "page_number": chunk.page_number,
                            "chunk_index": chunk.chunk_index,
                            "text": chunk.text,
                            "char_start": chunk.char_start,
                            "char_end": chunk.char_end,
                            "token_count_estimate": chunk.token_count_estimate,
                            "metadata": json.dumps(chunk.metadata or {}),
                            "embedding": emb_str,
                        },
                    )
            logger.info(f"Successfully upserted {len(chunks)} chunks into pgvector '{collection_name}'")
            return len(chunks)
        except Exception as e:
            logger.error(f"Failed to upsert chunks into pgvector '{collection_name}': {e}")
            raise VectorStorageError(f"pgvector upsert failed: {str(e)}")

    def search_similar(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        doc_id_filter: Optional[str] = None,
        filename_filter: Optional[str] = None,
        page_number_filter: Optional[int] = None,
        custom_filter: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        """Perform vector similarity search in pgvector using cosine distance."""
        emb_str = f"[{','.join(str(float(x)) for x in query_vector)}]"
        where_clauses = ["1=1"]
        params: Dict[str, Any] = {"query_emb": emb_str, "top_k": top_k}

        if doc_id_filter:
            where_clauses.append("doc_id = :doc_id")
            params["doc_id"] = doc_id_filter
        if filename_filter:
            where_clauses.append("filename = :filename")
            params["filename"] = filename_filter
        if page_number_filter is not None:
            where_clauses.append("page_number = :page_number")
            params["page_number"] = page_number_filter
        if custom_filter:
            for i, (k, v) in enumerate(custom_filter.items()):
                param_key = f"cfilter_{i}"
                where_clauses.append(f"metadata->>'{k}' = :{param_key}")
                params[param_key] = str(v)

        where_sql = " AND ".join(where_clauses)
        # Cosine distance operator in pgvector is <=> (0 = identical, 2 = opposite).
        # Cosine similarity is 1.0 - (embedding <=> query_vector).
        query_sql = f"""
            SELECT
                chunk_id, doc_id, filename, page_number, chunk_index,
                text, char_start, char_end, token_count_estimate, metadata,
                1.0 - (embedding <=> :query_emb::vector) AS score
            FROM {collection_name}
            WHERE {where_sql}
            ORDER BY embedding <=> :query_emb::vector ASC
            LIMIT :top_k;
        """

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query_sql), params)
                rows = result.fetchall()

            chunks: List[RetrievedChunk] = []
            for row in rows:
                score = float(row[10]) if row[10] is not None else 0.0
                if score_threshold is not None and score < score_threshold:
                    continue

                raw_meta = row[9]
                metadata = raw_meta if isinstance(raw_meta, dict) else (json.loads(raw_meta) if raw_meta else {})

                chunks.append(
                    RetrievedChunk(
                        chunk_id=str(row[0]),
                        doc_id=str(row[1]),
                        filename=str(row[2]),
                        page_number=int(row[3]),
                        chunk_index=int(row[4]),
                        text=str(row[5]),
                        score=score,
                        metadata=metadata,
                    )
                )

            logger.info(f"pgvector retrieved {len(chunks)} chunks (top_k={top_k}, threshold={score_threshold})")
            return chunks
        except Exception as e:
            logger.error(f"pgvector similarity search failed on '{collection_name}': {e}")
            raise VectorStorageError(f"pgvector similarity search failed: {str(e)}")

    def delete_document(self, collection_name: str, doc_id: str) -> int:
        """Delete all chunks for a document from pgvector."""
        try:
            delete_sql = text(f"DELETE FROM {collection_name} WHERE doc_id = :doc_id;")
            with self.engine.begin() as conn:
                res = conn.execute(delete_sql, {"doc_id": doc_id})
                deleted = res.rowcount
            logger.info(f"Deleted {deleted} chunks for doc_id='{doc_id}' from pgvector '{collection_name}'")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete document '{doc_id}' from pgvector: {e}")
            raise VectorStorageError(f"pgvector delete failed: {str(e)}")

    def list_documents(self, collection_name: str) -> List[Dict[str, Any]]:
        """List distinct documents with aggregated chunk counts from pgvector."""
        try:
            query_sql = f"""
                SELECT
                    doc_id,
                    filename,
                    COUNT(DISTINCT page_number) AS page_count,
                    COUNT(*) AS chunk_count
                FROM {collection_name}
                GROUP BY doc_id, filename;
            """
            with self.engine.connect() as conn:
                res = conn.execute(text(query_sql))
                rows = res.fetchall()

            docs = []
            for r in rows:
                filename = str(r[1])
                file_type = Path(filename).suffix.replace(".", "") or "txt"
                docs.append({
                    "doc_id": str(r[0]),
                    "filename": filename,
                    "file_type": file_type,
                    "page_count": int(r[2]),
                    "chunk_count": int(r[3]),
                })
            return docs
        except Exception as e:
            logger.error(f"Failed to list documents from pgvector: {e}")
            raise VectorStorageError(f"pgvector list_documents failed: {str(e)}")

    def get_document_chunks(self, collection_name: str, doc_id: str) -> List[DocumentChunk]:
        """Fetch all chunks for a specific document ordered by chunk_index."""
        try:
            query_sql = text(f"""
                SELECT
                    chunk_id, doc_id, filename, page_number, chunk_index,
                    text, char_start, char_end, token_count_estimate, metadata
                FROM {collection_name}
                WHERE doc_id = :doc_id
                ORDER BY chunk_index ASC;
            """)
            with self.engine.connect() as conn:
                res = conn.execute(query_sql, {"doc_id": doc_id})
                rows = res.fetchall()

            chunks: List[DocumentChunk] = []
            for r in rows:
                raw_meta = r[9]
                meta = raw_meta if isinstance(raw_meta, dict) else (json.loads(raw_meta) if raw_meta else {})
                chunks.append(
                    DocumentChunk(
                        chunk_id=str(r[0]),
                        doc_id=str(r[1]),
                        filename=str(r[2]),
                        page_number=int(r[3]),
                        chunk_index=int(r[4]),
                        text=str(r[5]),
                        char_start=int(r[6] or 0),
                        char_end=int(r[7] or 0),
                        token_count_estimate=int(r[8] or 0),
                        metadata=meta,
                    )
                )
            return chunks
        except Exception as e:
            logger.error(f"Failed to get chunks for doc_id='{doc_id}' from pgvector: {e}")
            raise VectorStorageError(f"pgvector get_document_chunks failed: {str(e)}")

    def get_all_chunks(self, collection_name: str) -> List[DocumentChunk]:
        """Fetch all indexed chunks across pgvector table for BM25 lexical indexing."""
        try:
            query_sql = text(f"""
                SELECT
                    chunk_id, doc_id, filename, page_number, chunk_index,
                    text, char_start, char_end, token_count_estimate, metadata
                FROM {collection_name}
                ORDER BY id ASC;
            """)
            with self.engine.connect() as conn:
                res = conn.execute(query_sql)
                rows = res.fetchall()

            chunks: List[DocumentChunk] = []
            for r in rows:
                raw_meta = r[9]
                meta = raw_meta if isinstance(raw_meta, dict) else (json.loads(raw_meta) if raw_meta else {})
                chunks.append(
                    DocumentChunk(
                        chunk_id=str(r[0]),
                        doc_id=str(r[1]),
                        filename=str(r[2]),
                        page_number=int(r[3]),
                        chunk_index=int(r[4]),
                        text=str(r[5]),
                        char_start=int(r[6] or 0),
                        char_end=int(r[7] or 0),
                        token_count_estimate=int(r[8] or 0),
                        metadata=meta,
                    )
                )
            return chunks
        except Exception as e:
            logger.error(f"Failed to scroll all chunks from pgvector: {e}")
            raise VectorStorageError(f"pgvector get_all_chunks failed: {str(e)}")

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection metrics (total vectors, indexed points, status)."""
        try:
            query_sql = text(f"SELECT COUNT(*) FROM {collection_name};")
            with self.engine.connect() as conn:
                res = conn.execute(query_sql)
                count = int(res.scalar() or 0)

            return {
                "collection_name": collection_name,
                "status": "green",
                "vectors_count": count,
                "points_count": count,
                "backend": "supabase_pgvector",
            }
        except Exception as e:
            logger.warning(f"Could not get pgvector collection info for '{collection_name}': {e}")
            return {
                "collection_name": collection_name,
                "status": "unknown",
                "backend": "supabase_pgvector",
                "error": str(e),
            }
