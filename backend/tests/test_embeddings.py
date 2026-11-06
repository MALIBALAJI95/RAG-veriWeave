"""Unit tests for embedding models."""

from backend.app.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from backend.tests.conftest import MockDeterministicEmbeddings


def test_mock_embeddings():
    embedder = MockDeterministicEmbeddings(dimension=128)
    assert embedder.dimension == 128

    vecs = embedder.embed_documents(["Hello world", "Artificial intelligence"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 128

    query_vec = embedder.embed_query("Query test")
    assert len(query_vec) == 128


def test_sentence_transformer_embeddings_real():
    # Test real lightweight Sentence Transformer model
    embedder = SentenceTransformerEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        device="cpu",
    )
    assert embedder.dimension == 384

    texts = [
        "Retrieval-Augmented Generation bridges vector similarity with LLM synthesis.",
        "Qdrant provides persistent, high-performance vector indexing.",
    ]
    vectors = embedder.embed_documents(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384

    # Verify cosine normalization (sum of squares == 1.0)
    norm = sum(x**2 for x in vectors[0])
    assert abs(norm - 1.0) < 1e-4

    q_vec = embedder.embed_query("What is RAG?")
    assert len(q_vec) == 384
