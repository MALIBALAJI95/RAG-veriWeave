"""Adaptive & Corrective RAG package exports."""

from backend.app.adaptive.schemas import (
    AdaptiveRAGState,
    AdaptiveWorkflowMetadata,
    EvidenceRelevanceGrade,
    GroundingValidationResult,
    QueryRewriteResult,
)

__all__ = [
    "EvidenceRelevanceGrade",
    "QueryRewriteResult",
    "GroundingValidationResult",
    "AdaptiveWorkflowMetadata",
    "AdaptiveRAGState",
    "EvidenceRelevanceGrader",
    "AdaptiveQueryRewriter",
    "GroundingValidator",
    "AdaptiveRAGWorkflow",
]


def __getattr__(name: str):
    if name == "EvidenceRelevanceGrader":
        from backend.app.adaptive.relevance_grader import EvidenceRelevanceGrader
        return EvidenceRelevanceGrader
    if name == "AdaptiveQueryRewriter":
        from backend.app.adaptive.query_rewriter import AdaptiveQueryRewriter
        return AdaptiveQueryRewriter
    if name == "GroundingValidator":
        from backend.app.adaptive.grounding_validator import GroundingValidator
        return GroundingValidator
    if name == "AdaptiveRAGWorkflow":
        from backend.app.adaptive.workflow import AdaptiveRAGWorkflow
        return AdaptiveRAGWorkflow
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
