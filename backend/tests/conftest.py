"""Pytest fixtures and test environment configuration."""

import shutil
from pathlib import Path
from typing import Generator, List
import pytest
from fastapi.testclient import TestClient
from backend.app.api.deps import (
    get_embedding_model,
    get_ingestion_pipeline,
    get_retriever,
    get_settings,
    get_storage_manager,
)
from backend.app.core.config import Settings
from backend.app.embeddings.base import BaseEmbeddings
from backend.app.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from backend.app.generation.ollama_client import OllamaClient
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.main import app
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.storage.qdrant_client import QdrantStorageManager


class MockDeterministicEmbeddings(BaseEmbeddings):
    """Deterministic fast mock embedding model for rapid testing without downloading weights."""

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        results = []
        for text in texts:
            # Deterministic pseudo-embedding from text length and hash
            val = (len(text) % 100) / 100.0
            vec = [val] * self._dim
            # Normalize vector
            norm = sum(x**2 for x in vec) ** 0.5 or 1.0
            results.append([x / norm for x in vec])
        return results

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


@pytest.fixture(scope="session")
def sample_docs_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "datasets" / "sample_docs"


@pytest.fixture(scope="session")
def sample_pdf_path(sample_docs_dir: Path) -> Path:
    return sample_docs_dir / "rag_architectures.pdf"


@pytest.fixture(scope="session")
def sample_docx_path(sample_docs_dir: Path) -> Path:
    return sample_docs_dir / "retrieval_strategies.docx"


@pytest.fixture(scope="session")
def sample_txt_path(sample_docs_dir: Path) -> Path:
    return sample_docs_dir / "ai_agents_overview.txt"


@pytest.fixture
def temp_dir(tmp_path: Path) -> Generator[Path, None, None]:
    yield tmp_path
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture
def test_storage(temp_dir: Path) -> Generator[QdrantStorageManager, None, None]:
    storage_path = temp_dir / "qdrant"
    manager = QdrantStorageManager(storage_path=storage_path)
    manager.ensure_collection("test_collection", vector_size=384)
    yield manager


@pytest.fixture
def mock_embeddings() -> BaseEmbeddings:
    return MockDeterministicEmbeddings(dimension=384)


@pytest.fixture
def test_pipeline(
    test_storage: QdrantStorageManager,
    mock_embeddings: BaseEmbeddings,
    temp_dir: Path,
) -> IngestionPipeline:
    return IngestionPipeline(
        storage_manager=test_storage,
        embedding_model=mock_embeddings,
        chunk_size=300,
        chunk_overlap=50,
        documents_dir=temp_dir / "documents",
        collection_name="test_collection",
    )


@pytest.fixture
def client(
    test_storage: QdrantStorageManager,
    mock_embeddings: BaseEmbeddings,
    temp_dir: Path,
) -> Generator[TestClient, None, None]:
    """TestClient with isolated storage and deterministic mock embeddings."""
    test_settings = Settings(
        QDRANT_STORAGE_PATH=temp_dir / "qdrant",
        DOCUMENTS_DIR=temp_dir / "documents",
        QDRANT_COLLECTION_NAME="test_collection",
        ENABLE_FALLBACK_GENERATOR=True,
    )

    pipeline = IngestionPipeline(
        storage_manager=test_storage,
        embedding_model=mock_embeddings,
        chunk_size=300,
        chunk_overlap=50,
        documents_dir=temp_dir / "documents",
        collection_name="test_collection",
    )

    retriever = SimilarityRetriever(
        storage_manager=test_storage,
        embedding_model=mock_embeddings,
        collection_name="test_collection",
    )

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_storage_manager] = lambda: test_storage
    app.dependency_overrides[get_embedding_model] = lambda: mock_embeddings
    app.dependency_overrides[get_ingestion_pipeline] = lambda: pipeline
    app.dependency_overrides[get_retriever] = lambda: retriever

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
