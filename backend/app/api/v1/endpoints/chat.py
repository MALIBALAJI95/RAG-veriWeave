"""Chat and retrieval-augmented question answering endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.api.deps import get_grounded_generator, get_retriever
from backend.app.core.logging import get_logger
from backend.app.generation.grounded_generator import GroundedAnswerGenerator
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.schemas.chat import ChatRequest, ChatResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question against indexed documents",
    description="Performs semantic retrieval against Qdrant and generates a grounded response with source citations.",
)
async def chat(
    request: ChatRequest,
    retriever: SimilarityRetriever = Depends(get_retriever),
    generator: GroundedAnswerGenerator = Depends(get_grounded_generator),
) -> ChatResponse:
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query string cannot be empty.",
        )

    try:
        # 1. Retrieve top-k relevant chunks
        retrieved_chunks = retriever.retrieve(
            query=query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            doc_id_filter=request.doc_id_filter,
        )

        # 2. Generate grounded response with citations
        response = generator.generate_grounded_answer(
            query=query,
            retrieved_chunks=retrieved_chunks,
        )
        return response
    except Exception as e:
        logger.error(f"Error processing chat query '{query[:50]}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat generation error: {str(e)}",
        )
