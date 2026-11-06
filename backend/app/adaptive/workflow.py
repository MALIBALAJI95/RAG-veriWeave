"""LangGraph-powered Adaptive & Corrective RAG stateful workflow."""

import time
from typing import Any, Dict, List, Optional
from langgraph.graph import END, StateGraph
from backend.app.adaptive.grounding_validator import GroundingValidator
from backend.app.adaptive.query_rewriter import AdaptiveQueryRewriter
from backend.app.adaptive.relevance_grader import EvidenceRelevanceGrader
from backend.app.adaptive.schemas import (
    AdaptiveRAGState,
    AdaptiveWorkflowMetadata,
    GroundingValidationResult,
)
from backend.app.core.logging import get_logger
from backend.app.generation.grounded_generator import GroundedAnswerGenerator
from backend.app.routing.evidence import EvidenceItem
from backend.app.routing.orchestrator import RoutingOrchestrator
from backend.app.routing.schemas import RouteCategory, RoutingDecision, RoutingMode
from backend.app.schemas.chat import (
    ChatResponse,
    Citation,
    MetadataFilter,
    RetrievalStrategy,
    RetrievedChunk,
)

logger = get_logger(__name__)


class AdaptiveRAGWorkflow:
    """Stateful LangGraph workflow implementing grading, query rewriting, and hallucination correction."""

    def __init__(
        self,
        routing_orchestrator: RoutingOrchestrator,
        relevance_grader: EvidenceRelevanceGrader,
        query_rewriter: AdaptiveQueryRewriter,
        grounding_validator: GroundingValidator,
        generator: GroundedAnswerGenerator,
        max_rewrites: int = 2,
        max_corrections: int = 2,
        min_relevant_evidence: int = 1,
    ):
        self.orchestrator = routing_orchestrator
        self.grader = relevance_grader
        self.rewriter = query_rewriter
        self.validator = grounding_validator
        self.generator = generator
        self.max_rewrites = max_rewrites
        self.max_corrections = max_corrections
        self.min_relevant = min_relevant_evidence

        # Build and compile LangGraph workflow
        self.workflow = self._build_graph()
        self.app = self.workflow.compile()

    def _build_graph(self) -> StateGraph:
        """Construct stateful workflow graph with explicit nodes and conditional edges."""
        graph = StateGraph(AdaptiveRAGState)

        # 1. Add Workflow Nodes
        graph.add_node("route_query", self._node_route_query)
        graph.add_node("retrieve_evidence", self._node_retrieve_evidence)
        graph.add_node("grade_evidence", self._node_grade_evidence)
        graph.add_node("rewrite_query", self._node_rewrite_query)
        graph.add_node("generate_answer", self._node_generate_answer)
        graph.add_node("validate_grounding", self._node_validate_grounding)
        graph.add_node("revise_answer", self._node_revise_answer)
        graph.add_node("finalize_response", self._node_finalize_response)

        # 2. Add Graph Edges
        graph.set_entry_point("route_query")
        graph.add_edge("route_query", "retrieve_evidence")
        graph.add_edge("retrieve_evidence", "grade_evidence")

        # Conditional Edge after grading: Sufficient evidence -> Generate, else Rewrite
        graph.add_conditional_edges(
            "grade_evidence",
            self._edge_check_evidence_sufficiency,
            {
                "generate": "generate_answer",
                "rewrite": "rewrite_query",
            },
        )

        # After rewrite, execute corrective retrieval cycle
        graph.add_edge("rewrite_query", "retrieve_evidence")

        # After generate, execute hallucination and citation validation
        graph.add_edge("generate_answer", "validate_grounding")

        # Conditional Edge after validation: Grounded -> Finalize, else Revise
        graph.add_conditional_edges(
            "validate_grounding",
            self._edge_check_grounding_validity,
            {
                "finalize": "finalize_response",
                "revise": "revise_answer",
            },
        )

        # After revision, re-validate
        graph.add_edge("revise_answer", "validate_grounding")

        # Terminal Edge
        graph.add_edge("finalize_response", END)

        return graph

    # =========================================================================
    # Workflow Nodes
    # =========================================================================

    def _node_route_query(self, state: AdaptiveRAGState) -> Dict[str, Any]:
        """Classify query intent across vector, SQL, web, or multi-source paths."""
        query = state["query"]
        mode = state.get("routing_mode", RoutingMode.AUTO)
        strategy = state.get("selected_strategy", RetrievalStrategy.BASELINE)

        decision = self.orchestrator.classifier.classify(
            query=query,
            routing_mode=mode,
            selected_strategy=strategy,
        )

        trace = list(state.get("workflow_trace", []))
        trace.append(f"route_query: selected='{decision.route.value}' (conf={decision.confidence:.2f})")

        return {
            "routing_decision": decision,
            "current_query": query,
            "workflow_trace": trace,
        }

    def _node_retrieve_evidence(self, state: AdaptiveRAGState) -> Dict[str, Any]:
        """Execute retrieval through existing Phase 3 RoutingOrchestrator."""
        current_query = state.get("current_query", state["query"])
        decision = state["routing_decision"]
        mode = state.get("routing_mode", RoutingMode.AUTO)
        strategy = state.get("selected_strategy", RetrievalStrategy.BASELINE)
        top_k = state.get("top_k", 4)
        score_thresh = state.get("score_threshold")
        rerank = state.get("rerank", False)
        filters = state.get("filters")
        doc_id_filter = state.get("doc_id_filter")

        new_evidence, _, _ = self.orchestrator.route_and_retrieve(
            query=current_query,
            routing_mode=mode,
            selected_strategy=decision.selected_strategy or strategy,
            top_k=top_k,
            score_threshold=score_thresh,
            rerank=rerank,
            filters=filters,
            doc_id_filter=doc_id_filter,
        )

        # Merge with existing evidence if any, preserving uniqueness
        existing_evidence = state.get("evidence", [])
        combined = list(existing_evidence)
        seen_source_ids = {e.source_id for e in combined}

        for item in new_evidence:
            if item.source_id not in seen_source_ids:
                seen_source_ids.add(item.source_id)
                combined.append(item)

        trace = list(state.get("workflow_trace", []))
        trace.append(
            f"retrieve_evidence: fetched {len(new_evidence)} new items (total {len(combined)}) "
            f"for query='{current_query[:40]}...'"
        )

        return {
            "evidence": combined,
            "workflow_trace": trace,
        }

    def _node_grade_evidence(self, state: AdaptiveRAGState) -> Dict[str, Any]:
        """Grade retrieved evidence items for semantic relevance."""
        query = state["query"]
        evidence = state.get("evidence", [])

        grades, relevant, irrelevant = self.grader.grade_evidence(
            query=query,
            evidence_items=evidence,
        )

        trace = list(state.get("workflow_trace", []))
        trace.append(f"grade_evidence: {len(relevant)}/{len(evidence)} relevant items")

        return {
            "graded_evidence": grades,
            "relevant_evidence": relevant,
            "irrelevant_evidence": irrelevant,
            "workflow_trace": trace,
        }

    def _node_rewrite_query(self, state: AdaptiveRAGState) -> Dict[str, Any]:
        """Reformulate query to overcome vocabulary mismatch or insufficient retrieval."""
        query = state["query"]
        rewrite_count = state.get("rewrite_count", 0) + 1
        history = list(state.get("rewritten_queries", []))

        rewrite_res = self.rewriter.rewrite(
            original_query=query,
            attempt_number=rewrite_count,
            failure_reason="Insufficient relevant evidence retrieved in prior cycle.",
        )
        history.append(rewrite_res.rewritten_query)

        trace = list(state.get("workflow_trace", []))
        trace.append(f"rewrite_query: attempt {rewrite_count} -> '{rewrite_res.rewritten_query}'")

        return {
            "current_query": rewrite_res.rewritten_query,
            "rewritten_queries": history,
            "rewrite_count": rewrite_count,
            "workflow_trace": trace,
        }

    def _node_generate_answer(self, state: AdaptiveRAGState) -> Dict[str, Any]:
        """Generate answer grounded in relevant evidence."""
        query = state["query"]
        relevant = state.get("relevant_evidence", [])
        retrieval_meta = self.orchestrator.vector_handler.last_metadata

        # If zero relevant evidence after exhausting retries
        if not relevant:
            answer = (
                "The available documents and knowledge sources do not contain sufficient verified "
                "information to answer this question. Please upload relevant files or refine your query."
            )
            citations = []
            trace = list(state.get("workflow_trace", []))
            trace.append("generate_answer: generated insufficient evidence declaration")
            return {
                "answer": answer,
                "citations": citations,
                "insufficient_evidence": True,
                "model_used": self.generator.client.model,
                "workflow_trace": trace,
            }

        response = self.generator.generate_grounded_answer(
            query=query,
            retrieved_chunks=[],
            retrieval_metadata=retrieval_meta,
            evidence_items=relevant,
        )

        trace = list(state.get("workflow_trace", []))
        trace.append(f"generate_answer: generated answer with {len(response.citations)} citations")

        return {
            "answer": response.answer,
            "citations": response.citations,
            "insufficient_evidence": False,
            "model_used": response.model_used,
            "workflow_trace": trace,
        }

    def _node_validate_grounding(self, state: AdaptiveRAGState) -> Dict[str, Any]:
        """Validate answer claims and citation integrity."""
        query = state["query"]
        answer = state.get("answer", "")
        relevant = state.get("relevant_evidence", [])
        citations = state.get("citations", [])
        corr_count = state.get("correction_count", 0)

        val_res = self.validator.validate(
            query=query,
            answer=answer,
            evidence_items=relevant,
            citations=citations,
            attempt_number=corr_count + 1,
        )

        trace = list(state.get("workflow_trace", []))
        trace.append(
            f"validate_grounding: grounded={val_res.is_grounded}, "
            f"citations_valid={val_res.citation_valid}"
        )

        return {
            "validation_result": val_res,
            "workflow_trace": trace,
        }

    def _node_revise_answer(self, state: AdaptiveRAGState) -> Dict[str, Any]:
        """Revise answer to eliminate unsupported claims detected during validation."""
        query = state["query"]
        answer = state.get("answer", "")
        val_res = state.get("validation_result")
        corr_count = state.get("correction_count", 0) + 1
        relevant = state.get("relevant_evidence", [])

        # Formulate grounded corrective revision
        if val_res and val_res.unsupported_claims:
            # If multiple corrections failed, safely default to strictly verified facts only
            if corr_count >= self.max_corrections:
                revised_answer = (
                    "Based strictly on verified source documents: "
                    + (" ".join([e.content_excerpt[:150] for e in relevant[:2]]))
                )
            else:
                # Remove ungrounded claims or regenerate
                resp = self.generator.generate_grounded_answer(
                    query=f"{query} (Answer strictly using only explicit facts from context)",
                    retrieved_chunks=[],
                    evidence_items=relevant,
                )
                revised_answer = resp.answer
        else:
            revised_answer = answer

        trace = list(state.get("workflow_trace", []))
        trace.append(f"revise_answer: applied correction attempt {corr_count}")

        return {
            "answer": revised_answer,
            "correction_count": corr_count,
            "workflow_trace": trace,
        }

    def _node_finalize_response(self, state: AdaptiveRAGState) -> Dict[str, Any]:
        """Package final workflow state."""
        trace = list(state.get("workflow_trace", []))
        trace.append("finalize_response: workflow complete")
        return {
            "status": "completed",
            "workflow_trace": trace,
        }

    # =========================================================================
    # Conditional Edges
    # =========================================================================

    def _edge_check_evidence_sufficiency(self, state: AdaptiveRAGState) -> str:
        """Decide whether retrieved evidence is sufficient or requires query reformulation."""
        relevant = state.get("relevant_evidence", [])
        rewrite_count = state.get("rewrite_count", 0)

        if len(relevant) >= self.min_relevant:
            return "generate"

        if rewrite_count < self.max_rewrites:
            return "rewrite"

        # Max rewrites reached, generate with what exists (or declare insufficiency)
        return "generate"

    def _edge_check_grounding_validity(self, state: AdaptiveRAGState) -> str:
        """Decide whether answer is faithful or requires correction."""
        if state.get("insufficient_evidence", False):
            return "finalize"

        val = state.get("validation_result")
        corr_count = state.get("correction_count", 0)

        if not val or (val.is_grounded and val.citation_valid):
            return "finalize"

        if corr_count < self.max_corrections:
            return "revise"

        return "finalize"

    # =========================================================================
    # Public Execution Entrypoint
    # =========================================================================

    def run(
        self,
        query: str,
        routing_mode: RoutingMode = RoutingMode.AUTO,
        selected_strategy: RetrievalStrategy = RetrievalStrategy.BASELINE,
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        rerank: bool = False,
        filters: Optional[MetadataFilter] = None,
        doc_id_filter: Optional[str] = None,
    ) -> ChatResponse:
        """Execute full LangGraph Adaptive & Corrective RAG workflow and return structured ChatResponse."""
        start_time = time.perf_counter()

        initial_state: AdaptiveRAGState = {
            "query": query,
            "current_query": query,
            "routing_mode": routing_mode,
            "selected_strategy": selected_strategy,
            "top_k": top_k,
            "score_threshold": score_threshold,
            "rerank": rerank,
            "filters": filters,
            "doc_id_filter": doc_id_filter,
            "evidence": [],
            "graded_evidence": [],
            "relevant_evidence": [],
            "irrelevant_evidence": [],
            "rewritten_queries": [],
            "rewrite_count": 0,
            "correction_count": 0,
            "workflow_trace": ["workflow_start"],
            "insufficient_evidence": False,
            "status": "in_progress",
        }

        # Invoke compiled LangGraph application
        final_state: AdaptiveRAGState = self.app.invoke(initial_state)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Construct AdaptiveWorkflowMetadata
        dec = final_state.get("routing_decision")
        route_str = dec.route.value if dec else "vector_document"

        adaptive_meta = AdaptiveWorkflowMetadata(
            adaptive_applied=True,
            route_selected=route_str,
            original_query=query,
            rewritten_queries=final_state.get("rewritten_queries", []),
            retrieved_evidence_count=len(final_state.get("evidence", [])),
            relevant_evidence_count=len(final_state.get("relevant_evidence", [])),
            irrelevant_evidence_count=len(final_state.get("irrelevant_evidence", [])),
            retrieval_attempts=final_state.get("rewrite_count", 0) + 1,
            correction_attempts=final_state.get("correction_count", 0),
            grounding_validation=final_state.get("validation_result"),
            workflow_trace=final_state.get("workflow_trace", []),
            latency_ms=round(elapsed_ms, 2),
        )

        # Build final RetrievedChunk representation for vector chunks if any
        chunks_for_response: List[RetrievedChunk] = []
        for e in final_state.get("relevant_evidence", []):
            if e.source_type == "vector_document":
                chunks_for_response.append(
                    RetrievedChunk(
                        chunk_id=e.source_id,
                        doc_id=e.doc_id or "doc",
                        filename=e.filename or "unknown",
                        page_number=e.page_number or 1,
                        chunk_index=e.chunk_index or 0,
                        text=e.content_excerpt,
                        score=e.score,
                        metadata=e.metadata,
                    )
                )

        return ChatResponse(
            query=query,
            answer=final_state.get("answer", ""),
            citations=final_state.get("citations", []),
            retrieved_chunks=chunks_for_response,
            model_used=final_state.get("model_used", self.generator.client.model),
            latency_ms=round(elapsed_ms, 2),
            grounded=bool(final_state.get("validation_result", {}).is_grounded if final_state.get("validation_result") else True),
            fallback_used=final_state.get("insufficient_evidence", False),
            routing_decision=final_state.get("routing_decision"),
            retrieval_metadata=self.orchestrator.vector_handler.last_metadata,
            evidence=final_state.get("relevant_evidence", []),
            adaptive_metadata=adaptive_meta,
        )
