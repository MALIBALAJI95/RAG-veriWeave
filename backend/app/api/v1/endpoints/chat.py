"""Chat, intelligent multi-path routing, and adaptive corrective RAG endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.adaptive.workflow import AdaptiveRAGWorkflow
from backend.app.api.deps import (
    get_adaptive_workflow,
    get_grounded_generator,
    get_routing_orchestrator,
)
from backend.app.core.logging import get_logger
from backend.app.generation.grounded_generator import GroundedAnswerGenerator
from backend.app.routing.orchestrator import RoutingOrchestrator
from backend.app.routing.schemas import RoutingMode
from backend.app.schemas.chat import ChatRequest, ChatResponse, RetrievalStrategy

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question with intelligent multi-path routing or adaptive corrective RAG",
    description=(
        "Executes question answering using either standard multi-path routing (vector, SQL, web, multi-source) "
        "or an adaptive self-correcting LangGraph workflow (`adaptive=true`) featuring evidence grading, "
        "query rewriting, corrective retrieval, and hallucination validation."
    ),
)
async def chat(
    request: ChatRequest,
    orchestrator: RoutingOrchestrator = Depends(get_routing_orchestrator),
    generator: GroundedAnswerGenerator = Depends(get_grounded_generator),
    adaptive_workflow: AdaptiveRAGWorkflow = Depends(get_adaptive_workflow),
) -> ChatResponse:
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query string cannot be empty.",
        )

    routing_mode = request.routing_mode or RoutingMode.AUTO
    strategy = request.retrieval_strategy or RetrievalStrategy.BASELINE

    try:
        # 1. Execute Adaptive & Corrective LangGraph workflow if requested
        if request.adaptive:
            logger.info(f"Executing LangGraph Adaptive & Corrective RAG workflow for query: '{query[:40]}...'")
            response = adaptive_workflow.run(
                query=query,
                routing_mode=routing_mode,
                selected_strategy=strategy,
                top_k=request.top_k,
                score_threshold=request.score_threshold,
                rerank=request.rerank or False,
                filters=request.filters,
                doc_id_filter=request.doc_id_filter,
            )
            return response

        # 2. Standard Multi-Path Routing & Retrieval (Phase 3 flow)
        evidence, decision, exec_meta = orchestrator.route_and_retrieve(
            query=query,
            routing_mode=routing_mode,
            selected_strategy=strategy,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            rerank=request.rerank or False,
            filters=request.filters,
            doc_id_filter=request.doc_id_filter,
        )

        retrieval_meta = orchestrator.vector_handler.last_metadata

        # 3. Generate grounded response with multi-source citations
        response = generator.generate_grounded_answer(
            query=query,
            retrieved_chunks=[],
            retrieval_metadata=retrieval_meta,
            evidence_items=evidence,
        )

        # 4. Attach routing decision and cross-source evidence
        response.routing_decision = decision
        response.evidence = evidence

        return response
    except Exception as e:
        logger.error(f"Error processing chat query '{query[:50]}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat generation error: {str(e)}",
        )
