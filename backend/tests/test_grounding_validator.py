"""Tests for grounding, hallucination detection, and citation validation."""

import pytest
from backend.app.adaptive.grounding_validator import GroundingValidator
from backend.app.routing.evidence import EvidenceItem
from backend.app.schemas.chat import Citation


@pytest.fixture
def verified_evidence():
    return [
        EvidenceItem(
            evidence_id="ev_doc_1",
            source_type="vector_document",
            source_id="chunk_01",
            doc_id="doc_rag",
            filename="rag_architectures.pdf",
            page_number=2,
            chunk_index=0,
            title="rag_architectures.pdf",
            content_excerpt="VeriWeave implements hybrid search fusing dense vectors and BM25 lexical retrieval using Reciprocal Rank Fusion.",
            score=0.91,
        )
    ]


def test_grounding_validator_detects_grounded_answer(verified_evidence):
    """GroundingValidator must confirm answers whose claims are directly supported by evidence."""
    validator = GroundingValidator(ollama_client=None)
    query = "How does VeriWeave implement hybrid search?"
    answer = (
        "VeriWeave implements hybrid search fusing dense vectors and BM25 lexical retrieval using Reciprocal Rank Fusion."
    )
    citations = [
        Citation(
            citation_id=1,
            doc_id="doc_rag",
            filename="rag_architectures.pdf",
            page_number=2,
            chunk_index=0,
            score=0.91,
            snippet="VeriWeave implements hybrid search fusing dense vectors and BM25...",
        )
    ]

    res = validator.validate(query, answer, verified_evidence, citations)

    assert res.is_grounded is True
    assert res.citation_valid is True
    assert len(res.unsupported_claims) == 0
    assert len(res.supported_claims) >= 1


def test_grounding_validator_detects_hallucinations(verified_evidence):
    """GroundingValidator must detect and flag unsupported claims not found in retrieved evidence."""
    validator = GroundingValidator(ollama_client=None)
    query = "How does VeriWeave implement hybrid search?"
    # Answer hallucinates completely unsupported claims about quantum cryptography and blockchain
    hallucinated_answer = (
        "VeriWeave implements quantum teleportation cryptography on the Ethereum blockchain to synchronize satellite nodes."
    )
    citations = [
        Citation(
            citation_id=1,
            doc_id="doc_rag",
            filename="rag_architectures.pdf",
            page_number=2,
            chunk_index=0,
            score=0.91,
            snippet="VeriWeave implements hybrid search...",
        )
    ]

    res = validator.validate(query, hallucinated_answer, verified_evidence, citations)

    assert res.is_grounded is False
    assert len(res.unsupported_claims) >= 1


def test_grounding_validator_detects_invalid_citations(verified_evidence):
    """GroundingValidator must flag citations that point to non-existent document sources."""
    validator = GroundingValidator(ollama_client=None)
    query = "What is VeriWeave?"
    answer = "VeriWeave implements hybrid search fusing dense vectors."
    # Fabricated citation filename not in evidence
    invalid_citations = [
        Citation(
            citation_id=1,
            doc_id="fake_doc_id",
            filename="fabricated_paper_never_uploaded.pdf",
            page_number=99,
            chunk_index=5,
            score=0.99,
            snippet="Fabricated snippet",
        )
    ]

    res = validator.validate(query, answer, verified_evidence, invalid_citations)

    assert res.citation_valid is False
    assert res.is_grounded is False


def test_grounding_validator_truthful_insufficient_evidence():
    """GroundingValidator must consider a truthful declaration of insufficient evidence as grounded."""
    validator = GroundingValidator(ollama_client=None)
    query = "What is the secret recipe for immortality?"
    answer = "The provided documents do not contain sufficient information to answer this question."

    res = validator.validate(query, answer, [], [])

    assert res.is_grounded is True
    assert res.citation_valid is True
    assert len(res.unsupported_claims) == 0
