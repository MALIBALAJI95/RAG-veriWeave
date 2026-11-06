"""Tests for evidence relevance grading, deterministic scoring, and provenance preservation."""

import pytest
from backend.app.adaptive.relevance_grader import EvidenceRelevanceGrader
from backend.app.routing.evidence import EvidenceItem


@pytest.fixture
def sample_evidence():
    item_relevant = EvidenceItem(
        evidence_id="ev_rel_1",
        source_type="vector_document",
        source_id="chunk_101",
        doc_id="doc_rag_paper",
        filename="rag_paper.pdf",
        page_number=3,
        chunk_index=1,
        title="rag_paper.pdf",
        content_excerpt="Dense retrieval maps queries and documents into a shared continuous vector space using neural bi-encoders.",
        score=0.88,
        metadata={"custom_flag": "test_provenance"},
    )
    item_irrelevant = EvidenceItem(
        evidence_id="ev_irrel_1",
        source_type="vector_document",
        source_id="chunk_202",
        doc_id="doc_cooking",
        filename="italian_recipes.pdf",
        page_number=12,
        chunk_index=5,
        title="italian_recipes.pdf",
        content_excerpt="Bake the sourdough pizza dough at 450 degrees Fahrenheit until the mozzarella crust turns golden brown.",
        score=0.15,
    )
    return [item_relevant, item_irrelevant]


def test_relevance_grader_classifies_correctly(sample_evidence):
    """EvidenceRelevanceGrader must classify relevant vs irrelevant items accurately."""
    grader = EvidenceRelevanceGrader(ollama_client=None, default_threshold=0.50)
    query = "What is dense retrieval and how do neural bi-encoders work?"

    grades, relevant, irrelevant = grader.grade_evidence(query, sample_evidence)

    assert len(grades) == 2
    assert len(relevant) == 1
    assert len(irrelevant) == 1

    # Check relevant item
    assert relevant[0].evidence_id == "ev_rel_1"
    assert grades[0].is_relevant is True
    assert grades[0].score >= 0.50
    assert "dense" in grades[0].reason.lower() or "retrieval" in grades[0].reason.lower()

    # Check irrelevant item
    assert irrelevant[0].evidence_id == "ev_irrel_1"
    assert grades[1].is_relevant is False
    assert grades[1].score < 0.50


def test_relevance_grader_preserves_provenance(sample_evidence):
    """EvidenceRelevanceGrader must preserve original doc_id, filename, page_number, and metadata."""
    grader = EvidenceRelevanceGrader(ollama_client=None, default_threshold=0.50)
    query = "What is dense retrieval?"

    _, relevant, _ = grader.grade_evidence(query, sample_evidence)

    item = relevant[0]
    assert item.doc_id == "doc_rag_paper"
    assert item.filename == "rag_paper.pdf"
    assert item.page_number == 3
    assert item.chunk_index == 1
    assert item.metadata.get("custom_flag") == "test_provenance"


def test_relevance_grader_sql_evidence():
    """EvidenceRelevanceGrader must correctly evaluate structured SQL database records."""
    grader = EvidenceRelevanceGrader(ollama_client=None, default_threshold=0.50)
    sql_item = EvidenceItem(
        evidence_id="ev_sql_1",
        source_type="structured_sql",
        source_id="SELECT COUNT(*) FROM documents",
        content_excerpt="Query executed successfully. Result: {'total_documents': 42}",
        score=1.0,
        metadata={"sql_query": "SELECT COUNT(*) FROM documents"},
    )

    query = "How many documents are uploaded in the system?"
    grade = grader.grade_item(query, sql_item)

    assert grade.is_relevant is True
    assert grade.score >= 0.80
    assert grade.source_type == "structured_sql"
