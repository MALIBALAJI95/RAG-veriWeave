"""Chat and retrieval-augmented question answering endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.api.deps import get_grounded_generator, get_retrieval_orchestrator
from backend.app.core.logging import get_logger
from backend.app.generation.grounded_generator import GroundedAnswerGenerator
from backend.app.retrieval.orchestrator import RetrievalOrchestrator
from backend.app.schemas.chat import ChatRequest, ChatResponse, RetrievalStrategy

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question against indexed documents",
    description=(
        "Executes multi-strategy retrieval (baseline, multi_query, hyde, decomposition, fusion, "
        "hybrid, hybrid_rerank, rerank) and generates a strictly grounded answer with citations."
    ),
)
async def chat(
    request: ChatRequest,
    orchestrator: RetrievalOrchestrator = Depends(get_retrieval_orchestrator),
    generator: GroundedAnswerGenerator = Depends(get_grounded_generator),
) -> ChatResponse:
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query string cannot be empty.",
        )

    strategy = request.retrieval_strategy or RetrievalStrategy.BASELINE

    try:
        # 1. Execute multi-strategy retrieval through orchestrator
        retrieved_chunks, retrieval_meta = orchestrator.retrieve(
            query=query,
            strategy=strategy,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            rerank=request.rerank or False,
            doc_id_filter=request.doc_id_filter,
            filters=request.filters,
        )

        # 2. Generate grounded response with citations & retrieval metadata
        response = generator.generate_grounded_answer(
            query=query,
            retrieved_chunks=retrieved_chunks,
            retrieval_metadata=retrieval_meta,
        )
        return response
    except Exception as e:
        logger.error(f"Error processing chat query '{query[:50]}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat generation error: {str(e)}",
        )
