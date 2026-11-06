"""Pydantic schemas for documents, metadata, chunks, and ingestion responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata attached to an ingested document."""
    doc_id: str = Field(description="Unique identifier for the document (UUID)")
    filename: str = Field(description="Original filename uploaded by the user")
    file_type: str = Field(description="File extension or MIME type (e.g., pdf, docx, txt)")
    file_size_bytes: int = Field(description="File size in bytes")
    page_count: int = Field(default=1, description="Total number of pages or sections")
    chunk_count: int = Field(default=0, description="Total number of chunks produced")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of ingestion")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata")


class DocumentChunk(BaseModel):
    """Represents a discrete semantic chunk extracted from a document."""
    chunk_id: str = Field(description="Unique deterministic chunk ID (e.g., {doc_id}_{chunk_index})")
    doc_id: str = Field(description="Parent document ID")
    filename: str = Field(description="Parent document filename")
    page_number: int = Field(default=1, description="Page number where this chunk originated (1-indexed)")
    chunk_index: int = Field(description="Zero-indexed position of chunk within the document")
    text: str = Field(description="Extracted textual content of the chunk")
    char_start: int = Field(default=0, description="Character start offset in the original text/page")
    char_end: int = Field(default=0, description="Character end offset in the original text/page")
    token_count_estimate: int = Field(default=0, description="Estimated token count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary chunk metadata")


class IngestionResponse(BaseModel):
    """API response returned after successful document ingestion."""
    doc_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    status: str = "indexed"
    message: str = "Document successfully ingested, chunked, and indexed in Qdrant."


class DocumentDetail(BaseModel):
    """Summary details of an indexed document."""
    doc_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    created_at: datetime


class DocumentListResponse(BaseModel):
    """API response listing all indexed documents."""
    total: int
    documents: List[DocumentDetail]


class DocumentDeleteResponse(BaseModel):
    """API response after deleting a document."""
    doc_id: str
    filename: Optional[str] = None
    chunks_deleted: int
    status: str = "deleted"
    message: str = "Document successfully removed from vector storage and disk."
