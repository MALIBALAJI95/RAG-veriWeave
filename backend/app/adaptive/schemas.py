"""Pydantic schemas and state definitions for Phase 4 Adaptive & Corrective RAG."""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from backend.app.routing.evidence import EvidenceItem
from backend.app.routing.schemas import RoutingDecision, RoutingMode
from backend.app.schemas.chat import Citation, MetadataFilter
from backend.app.schemas.strategy import RetrievalStrategy


class EvidenceRelevanceGrade(BaseModel):
    """Relevance evaluation for a single retrieved evidence item."""
    evidence_id: str = Field(description="Identifier of the evaluated evidence item")
    is_relevant: bool = Field(description="Binary relevance decision")
    score: float = Field(ge=0.0, le=1.0, description="Relevance score (0.0 to 1.0)")
    reason: str = Field(description="Diagnostic reason for relevance classification")
    source_type: str = Field(default="vector_document", description="Origin of evidence")
    source_id: str = Field(default="", description="Original source identifier")


class QueryRewriteResult(BaseModel):
    """Result of adaptive query rewriting."""
    original_query: str = Field(description="Original user question")
    rewritten_query: str = Field(description="Reformulated question to optimize retrieval")
    rewrite_reason: str = Field(description="Explanation of why query was rewritten")
    attempt_number: int = Field(default=1, description="Sequential rewrite iteration")


class GroundingValidationResult(BaseModel):
    """Evaluation of generated answer faithfulness and citation validity."""
    is_grounded: bool = Field(description="Whether all factual claims are supported by evidence")
    supported_claims: List[str] = Field(default_factory=list, description="Verified claims with evidence backing")
    unsupported_claims: List[str] = Field(default_factory=list, description="Claims lacking retrieved evidence")
    citation_valid: bool = Field(default=True, description="Whether all citations reference real evidence items")
    missing_citations: List[str] = Field(default_factory=list, description="Statements requiring citation")
    validation_reason: str = Field(default="", description="Overall grounding assessment summary")
    attempt_number: int = Field(default=1, description="Sequential correction attempt")


class AdaptiveWorkflowMetadata(BaseModel):
    """Complete diagnostic metadata recording the execution of the LangGraph workflow."""
    adaptive_applied: bool = Field(default=True, description="Whether adaptive corrective workflow executed")
    route_selected: str = Field(default="vector_document", description="Initial routing decision")
    original_query: str = Field(description="Original query as submitted by user")
    rewritten_queries: List[str] = Field(default_factory=list, description="History of rewritten query iterations")
    retrieved_evidence_count: int = Field(default=0, description="Total raw evidence items retrieved")
    relevant_evidence_count: int = Field(default=0, description="Number of items graded as relevant")
    irrelevant_evidence_count: int = Field(default=0, description="Number of items graded as irrelevant")
    retrieval_attempts: int = Field(default=1, description="Number of retrieval cycles executed")
    correction_attempts: int = Field(default=0, description="Number of answer correction cycles executed")
    grounding_validation: Optional[GroundingValidationResult] = Field(
        default=None,
        description="Outcome of hallucination and citation validation",
    )
    workflow_trace: List[str] = Field(default_factory=list, description="Sequential trace of workflow node executions")
    latency_ms: float = Field(default=0.0, description="End-to-end execution latency in milliseconds")


class AdaptiveRAGState(TypedDict, total=False):
    """Stateful schema passed across LangGraph nodes and conditional edges."""
    query: str
    current_query: str
    routing_mode: RoutingMode
    selected_strategy: RetrievalStrategy
    top_k: int
    score_threshold: Optional[float]
    rerank: bool
    filters: Optional[MetadataFilter]
    doc_id_filter: Optional[str]
    routing_decision: Optional[RoutingDecision]
    evidence: List[EvidenceItem]
    graded_evidence: List[EvidenceRelevanceGrade]
    relevant_evidence: List[EvidenceItem]
    irrelevant_evidence: List[EvidenceItem]
    answer: Optional[str]
    citations: List[Citation]
    validation_result: Optional[GroundingValidationResult]
    rewritten_queries: List[str]
    rewrite_count: int
    correction_count: int
    workflow_trace: List[str]
    insufficient_evidence: bool
    status: str
    model_used: str
    latency_ms: float
