"""Tests for the LangGraph-powered Adaptive & Corrective RAG stateful workflow."""

from unittest.mock import MagicMock
import pytest
from backend.app.adaptive.grounding_validator import GroundingValidator
from backend.app.adaptive.query_rewriter import AdaptiveQueryRewriter
from backend.app.adaptive.relevance_grader import EvidenceRelevanceGrader
from backend.app.adaptive.workflow import AdaptiveRAGWorkflow
from backend.app.generation.grounded_generator import GroundedAnswerGenerator
from backend.app.generation.ollama_client import OllamaClient
from backend.app.routing.evidence import EvidenceItem
from backend.app.routing.orchestrator import RoutingOrchestrator
from backend.app.routing.schemas import RouteCategory, RoutingDecision, RoutingMode
from backend.app.schemas.chat import RetrievalStrategy


@pytest.fixture
def mock_orchestrator():
    orchestrator = MagicMock()
    # Mock classifier decision
    decision = RoutingDecision(
        route=RouteCategory.VECTOR_DOCUMENT,
        confidence=0.92,
        reasoning="Semantic document question.",
        classification_method="logical_rule",
        selected_strategy=RetrievalStrategy.HYBRID,
        required_sources=["vector_document"],
    )
    orchestrator.classifier.classify.return_value = decision

    # Mock vector handler last metadata
    orchestrator.vector_handler.last_metadata = None
    return orchestrator


def test_adaptive_workflow_direct_success(mock_orchestrator):
    """When retrieved evidence is immediately relevant, workflow proceeds directly to generation."""
    relevant_item = EvidenceItem(
        evidence_id="ev_test_1",
        source_type="vector_document",
        source_id="chunk_1",
        doc_id="doc_1",
        filename="ai_overview.pdf",
        page_number=1,
        chunk_index=0,
        title="ai_overview.pdf",
        content_excerpt="Autonomous agents perceive their environment through sensors and act via actuators.",
        score=0.95,
    )
    mock_orchestrator.route_and_retrieve.return_value = ([relevant_item], mock_orchestrator.classifier.classify.return_value, {})

    grader = EvidenceRelevanceGrader(ollama_client=None, default_threshold=0.50)
    rewriter = AdaptiveQueryRewriter(ollama_client=None, max_rewrites=2)
    validator = GroundingValidator(ollama_client=None)
    generator = GroundedAnswerGenerator(ollama_client=OllamaClient(enable_fallback=True))

    workflow = AdaptiveRAGWorkflow(
        routing_orchestrator=mock_orchestrator,
        relevance_grader=grader,
        query_rewriter=rewriter,
        grounding_validator=validator,
        generator=generator,
        max_rewrites=2,
    )

    query = "How do autonomous agents perceive their environment?"
    response = workflow.run(query=query)

    assert response.grounded is True
    assert response.adaptive_metadata is not None
    assert response.adaptive_metadata.adaptive_applied is True
    assert response.adaptive_metadata.retrieval_attempts == 1
    assert response.adaptive_metadata.relevant_evidence_count == 1
    assert len(response.adaptive_metadata.rewritten_queries) == 0
    assert any("route_query" in t for t in response.adaptive_metadata.workflow_trace)
    assert any("generate_answer" in t for t in response.adaptive_metadata.workflow_trace)


def test_adaptive_workflow_corrective_rewrite_cycle(mock_orchestrator):
    """When initial evidence is irrelevant, workflow rewrites query and triggers corrective retrieval."""
    irrelevant_item = EvidenceItem(
        evidence_id="ev_test_irrel",
        source_type="vector_document",
        source_id="chunk_irrel",
        doc_id="doc_recipes",
        filename="recipes.txt",
        page_number=1,
        chunk_index=0,
        title="recipes.txt",
        content_excerpt="Preheat oven to 350 degrees and whisk flour with sugar.",
        score=0.10,
    )
    relevant_item = EvidenceItem(
        evidence_id="ev_test_rel",
        source_type="vector_document",
        source_id="chunk_rel",
        doc_id="doc_agents",
        filename="agents.pdf",
        page_number=1,
        chunk_index=0,
        title="agents.pdf",
        content_excerpt="Autonomous agents perceive their environment using sensor inputs and choose actions.",
        score=0.92,
    )

    # First retrieval returns irrelevant; second retrieval returns relevant
    mock_orchestrator.route_and_retrieve.side_effect = [
        ([irrelevant_item], mock_orchestrator.classifier.classify.return_value, {}),
        ([relevant_item], mock_orchestrator.classifier.classify.return_value, {}),
    ]

    grader = EvidenceRelevanceGrader(ollama_client=None, default_threshold=0.50)
    rewriter = AdaptiveQueryRewriter(ollama_client=None, max_rewrites=2)
    validator = GroundingValidator(ollama_client=None)
    generator = GroundedAnswerGenerator(ollama_client=OllamaClient(enable_fallback=True))

    workflow = AdaptiveRAGWorkflow(
        routing_orchestrator=mock_orchestrator,
        relevance_grader=grader,
        query_rewriter=rewriter,
        grounding_validator=validator,
        generator=generator,
        max_rewrites=2,
    )

    query = "Can you please tell me how agents perceive their environment?"
    response = workflow.run(query=query)

    assert response.adaptive_metadata is not None
    assert response.adaptive_metadata.retrieval_attempts == 2
    assert len(response.adaptive_metadata.rewritten_queries) == 1
    assert any("rewrite_query" in t for t in response.adaptive_metadata.workflow_trace)


def test_adaptive_workflow_max_rewrites_insufficient_evidence(mock_orchestrator):
    """When evidence remains insufficient across all cycles, workflow terminates cleanly and declares insufficiency."""
    # Continual zero/irrelevant evidence
    mock_orchestrator.route_and_retrieve.return_value = ([], mock_orchestrator.classifier.classify.return_value, {})

    grader = EvidenceRelevanceGrader(ollama_client=None, default_threshold=0.50)
    rewriter = AdaptiveQueryRewriter(ollama_client=None, max_rewrites=2)
    validator = GroundingValidator(ollama_client=None)
    generator = GroundedAnswerGenerator(ollama_client=OllamaClient(enable_fallback=True))

    workflow = AdaptiveRAGWorkflow(
        routing_orchestrator=mock_orchestrator,
        relevance_grader=grader,
        query_rewriter=rewriter,
        grounding_validator=validator,
        generator=generator,
        max_rewrites=2,
        min_relevant_evidence=1,
    )

    query = "Nonexistent query about alien civilizations on Alpha Centauri"
    response = workflow.run(query=query)

    # Must terminate without infinite loop!
    assert response.adaptive_metadata is not None
    assert response.adaptive_metadata.retrieval_attempts == 3  # Initial + 2 rewrites
    assert response.adaptive_metadata.relevant_evidence_count == 0
    assert "insufficient" in response.answer.lower() or "not contain sufficient" in response.answer.lower()
    assert response.fallback_used is True
