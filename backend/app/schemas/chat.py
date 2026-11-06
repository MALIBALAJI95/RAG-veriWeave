"""Pydantic schemas for chat queries, citations, retrieved chunks, and responses."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Grounding source citation referencing document and page."""
    citation_id: int = Field(description="Sequential citation number (1, 2, ...)")
    doc_id: str = Field(description="Parent document UUID")
    filename: str = Field(description="Filename of the referenced source")
    page_number: int = Field(description="Page number (1-indexed)")
    chunk_index: int = Field(description="Index of the chunk in the document")
    score: float = Field(description="Similarity score (0.0 to 1.0)")
    snippet: str = Field(description="Representative excerpt from the source chunk")


class RetrievedChunk(BaseModel):
    """Raw chunk retrieved from vector database with relevance score."""
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """User request to query the RAG system."""
    query: str = Field(min_length=1, max_length=2000, description="User's natural language question")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of top chunks to retrieve")
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score filter (optional)",
    )
    doc_id_filter: Optional[str] = Field(
        default=None,
        description="Optional document ID to restrict retrieval scope",
    )


class ChatResponse(BaseModel):
    """Complete grounded answer returned to the user."""
    query: str
    answer: str
    citations: List[Citation]
    retrieved_chunks: List[RetrievedChunk]
    model_used: str
    latency_ms: float
    grounded: bool = True
    fallback_used: bool = False
