"""Automated unit and integration tests for Cloud Deployment & Compatibility."""

import os
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.database.session import init_db, reset_engine
from backend.app.embeddings.cloudflare_embeddings import CloudflareEmbeddings
from backend.app.generation.cloudflare_client import CloudflareWorkersAIClient
from backend.app.schemas.chat import RetrievedChunk
from backend.app.schemas.document import DocumentChunk
from backend.app.storage.factory import create_storage_manager
from backend.app.storage.qdrant_client import QdrantStorageManager
from backend.app.storage.supabase_pgvector import SupabasePgVectorStorageManager


class TestSettingsCloudConfig:
    """Test configuration resolving for cloud environments."""

    def test_database_url_normalization(self):
        settings = Settings(
            DATABASE_URL="postgres://user:pass@host:5432/dbname",
            VECTOR_STORAGE_BACKEND="pgvector",
        )
        assert settings.resolved_database_url == "postgresql://user:pass@host:5432/dbname"

    def test_supabase_db_url_precedence(self):
        settings = Settings(
            DATABASE_URL="postgresql://user:pass@host1:5432/db1",
            SUPABASE_DB_URL="postgresql://user:pass@host2:5432/db2",
        )
        assert settings.resolved_database_url == "postgresql://user:pass@host2:5432/db2"

    def test_empty_database_url(self):
        settings = Settings(DATABASE_URL=None, SUPABASE_DB_URL=None)
        assert settings.resolved_database_url is None


class TestStorageFactory:
    """Test storage manager selection between Qdrant and pgvector."""

    def test_default_storage_factory_is_qdrant(self, tmp_path):
        settings = Settings(
            QDRANT_STORAGE_PATH=tmp_path / "qdrant",
            VECTOR_STORAGE_BACKEND="qdrant",
        )
        storage = create_storage_manager(settings)
        assert isinstance(storage, QdrantStorageManager)

    def test_pgvector_without_db_url_falls_back_to_qdrant(self, tmp_path):
        settings = Settings(
            QDRANT_STORAGE_PATH=tmp_path / "qdrant",
            VECTOR_STORAGE_BACKEND="pgvector",
            DATABASE_URL=None,
            SUPABASE_DB_URL=None,
        )
        storage = create_storage_manager(settings)
        assert isinstance(storage, QdrantStorageManager)

    @patch("backend.app.storage.supabase_pgvector.create_engine")
    def test_pgvector_with_db_url_selects_supabase(self, mock_engine):
        settings = Settings(
            VECTOR_STORAGE_BACKEND="pgvector",
            DATABASE_URL="postgresql://user:secret@db.supabase.co:5432/postgres",
        )
        storage = create_storage_manager(settings)
        assert isinstance(storage, SupabasePgVectorStorageManager)


class TestCloudflareWorkersAIClient:
    """Test hosted Cloudflare Workers AI client and fallbacks."""

    def test_missing_credentials_health_check(self):
        client = CloudflareWorkersAIClient(account_id=None, api_token=None)
        reachable, details = client.check_health()
        assert not reachable
        assert details["provider"] == "cloudflare"
        assert details["fallback_active"] is True

    @patch("httpx.Client.post")
    def test_successful_health_check(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = CloudflareWorkersAIClient(
            account_id="1234567890abcdef1234567890abcdef",
            api_token="valid_token",
        )
        reachable, details = client.check_health()
        assert reachable is True
        assert details["reachable"] is True

    @patch("httpx.Client.post")
    def test_generation_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"response": "This is a cloud-hosted response."},
            "success": True,
        }
        mock_post.return_value = mock_response

        client = CloudflareWorkersAIClient(
            account_id="fake_account",
            api_token="fake_token",
            model="@cf/meta/llama-3.2-1b-instruct",
        )
        text, model, is_fallback = client.generate(prompt="What is VeriWeave?")
        assert text == "This is a cloud-hosted response."
        assert "cloudflare:" in model
        assert is_fallback is False

    def test_generation_fallback_when_offline(self):
        # Client without credentials with fallback enabled
        client = CloudflareWorkersAIClient(
            account_id=None,
            api_token=None,
            enable_fallback=True,
        )
        chunks = [
            RetrievedChunk(
                chunk_id="c1",
                doc_id="d1",
                filename="system.txt",
                page_number=1,
                chunk_index=0,
                text="VeriWeave is an adaptive retrieval engine with reliable grounded responses.",
                score=0.92,
            )
        ]
        text, model, is_fallback = client.generate(
            prompt="What is VeriWeave?",
            retrieved_chunks=chunks,
        )
        assert is_fallback is True
        assert "adaptive retrieval engine" in text
        assert "cloudflare-fallback" in model


class TestCloudflareEmbeddings:
    """Test hosted Cloudflare Embeddings provider."""

    def test_dimension(self):
        emb = CloudflareEmbeddings(dimension=384)
        assert emb.dimension == 384

    @patch("httpx.Client.post")
    def test_embed_documents_api_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "data": [
                    [0.1] * 384,
                    [0.2] * 384,
                ]
            },
            "success": True,
        }
        mock_post.return_value = mock_response

        emb = CloudflareEmbeddings(
            account_id="acc_id",
            api_token="token",
            fallback_local=False,
        )
        res = emb.embed_documents(["query one", "query two"])
        assert len(res) == 2
        assert len(res[0]) == 384

    def test_deterministic_hash_fallback(self):
        emb = CloudflareEmbeddings(account_id=None, api_token=None, fallback_local=False)
        res = emb.embed_documents(["hello world"])
        assert len(res) == 1
        assert len(res[0]) == 384
        # Verify it is normalized
        magnitude = sum(x * x for x in res[0]) ** 0.5
        assert abs(magnitude - 1.0) < 1e-4


class TestSupabasePgVectorStorageManager:
    """Test pgvector storage manager interface and SQL executions."""

    @patch("backend.app.storage.supabase_pgvector.create_engine")
    def test_manager_init_normalizes_url(self, mock_engine):
        mgr = SupabasePgVectorStorageManager("postgres://user:pass@host:5432/db")
        assert mgr.database_url == "postgresql://user:pass@host:5432/db"

    @patch("backend.app.storage.supabase_pgvector.create_engine")
    def test_ensure_collection_executes_ddl(self, mock_engine_factory):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin.return_value.__enter__.return_value = mock_conn
        mock_engine_factory.return_value = mock_engine

        mgr = SupabasePgVectorStorageManager("postgresql://user:pass@host:5432/db")
        mgr.ensure_collection("test_vectors", vector_size=384)

        # Confirm DDL operations were executed on connection
        assert mock_conn.execute.call_count >= 3

    @patch("backend.app.storage.supabase_pgvector.create_engine")
    def test_upsert_chunks(self, mock_engine_factory):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin.return_value.__enter__.return_value = mock_conn
        mock_engine_factory.return_value = mock_engine

        mgr = SupabasePgVectorStorageManager("postgresql://user:pass@host:5432/db")
        chunks = [
            DocumentChunk(
                chunk_id="chunk-1",
                doc_id="doc-1",
                filename="sample.txt",
                page_number=1,
                chunk_index=0,
                text="Cloud pgvector sample text",
            )
        ]
        embeddings = [[0.05] * 384]
        count = mgr.upsert_chunks("test_vectors", chunks, embeddings)
        assert count == 1
        assert mock_conn.execute.called

    @patch("backend.app.storage.supabase_pgvector.create_engine")
    def test_search_similar(self, mock_engine_factory):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        # Row format matching:
        # chunk_id, doc_id, filename, page_number, chunk_index, text, char_start, char_end, token_count_estimate, metadata, score
        mock_conn.execute.return_value.fetchall.return_value = [
            ("c1", "d1", "sample.txt", 1, 0, "Cloud pgvector sample text", 0, 26, 6, "{}", 0.95)
        ]
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_engine_factory.return_value = mock_engine

        mgr = SupabasePgVectorStorageManager("postgresql://user:pass@host:5432/db")
        results = mgr.search_similar("test_vectors", query_vector=[0.05] * 384, top_k=2)
        assert len(results) == 1
        assert results[0].chunk_id == "c1"
        assert results[0].score == 0.95


class TestProductionAPIHardening:
    """Test API size validation and optional API key middleware."""

    def test_upload_file_size_limit(self, client):
        from backend.app.core.config import get_settings
        settings = get_settings()

        # Create a mock upload file larger than limit
        large_bytes = b"X" * (settings.MAX_UPLOAD_SIZE_BYTES + 1024)
        files = {"file": ("big_doc.txt", large_bytes, "text/plain")}

        res = client.post("/api/v1/documents/upload", files=files)
        assert res.status_code == 413
        assert "exceeds maximum allowed upload size" in res.json()["detail"]
