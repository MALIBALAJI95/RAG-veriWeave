"""Unit tests for generation, prompt formatting, and citation verification."""

from backend.app.generation.grounded_generator import GroundedAnswerGenerator
from backend.app.generation.ollama_client import OllamaClient
from backend.app.generation.prompts import format_context_blocks
from backend.app.schemas.chat import RetrievedChunk


def test_format_context_blocks():
    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            doc_id="d1",
            filename="paper.pdf",
            page_number=3,
            chunk_index=0,
            text="Vector databases provide indexed nearest-neighbor search.",
            score=0.92,
        ),
        RetrievedChunk(
            chunk_id="c2",
            doc_id="d1",
            filename="paper.pdf",
            page_number=4,
            chunk_index=1,
            text="Cosine similarity compares angular distances.",
            score=0.88,
        ),
    ]

    context_str = format_context_blocks(chunks)
    assert "Reference Block [1]" in context_str
    assert "paper.pdf" in context_str
    assert "Page: 3" in context_str
    assert "Score: 0.920" in context_str
    assert "Vector databases provide" in context_str


def test_fallback_grounded_generator():
    client = OllamaClient(
        base_url="http://localhost:99999",  # unreachable port
        model="llama3.2:1b",
        enable_fallback=True,
    )
    generator = GroundedAnswerGenerator(ollama_client=client)

    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            doc_id="doc_alpha",
            filename="alpha_specs.pdf",
            page_number=2,
            chunk_index=0,
            text="The engine uses hierarchical navigable small world (HNSW) graphs.",
            score=0.95,
        )
    ]

    response = generator.generate_grounded_answer(
        query="What graph structure is used?",
        retrieved_chunks=chunks,
    )

    assert response.grounded is True
    assert response.fallback_used is True
    assert len(response.citations) == 1
    citation = response.citations[0]
    assert citation.citation_id == 1
    assert citation.doc_id == "doc_alpha"
    assert citation.filename == "alpha_specs.pdf"
    assert citation.page_number == 2
    assert citation.score == 0.95
    assert "HNSW" in citation.snippet
    assert "hierarchical navigable small world" in response.answer


def test_generator_no_chunks():
    client = OllamaClient(enable_fallback=True)
    generator = GroundedAnswerGenerator(ollama_client=client)

    response = generator.generate_grounded_answer(
        query="What is the meaning of life?",
        retrieved_chunks=[],
    )

    assert response.grounded is False
    assert len(response.citations) == 0
    assert "No relevant documents found" in response.answer
