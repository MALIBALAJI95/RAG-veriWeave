"""Domain-specific exceptions and error handlers."""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class VeriWeaveException(Exception):
    """Base exception for VeriWeave domain errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DocumentIngestionError(VeriWeaveException):
    """Raised when document loading or ingestion fails."""
    pass


class UnsupportedFileTypeError(VeriWeaveException):
    """Raised when an uploaded document type is not supported."""
    pass


class ExtractionError(VeriWeaveException):
    """Raised when text extraction from a file fails."""
    pass


class VectorStorageError(VeriWeaveException):
    """Raised when vector database operations fail."""
    pass


class EmbeddingError(VeriWeaveException):
    """Raised when embedding generation fails."""
    pass


class GenerationError(VeriWeaveException):
    """Raised when LLM answer generation fails."""
    pass


class DocumentNotFoundError(VeriWeaveException):
    """Raised when a requested document is not found."""
    pass


async def veriweave_exception_handler(request: Request, exc: VeriWeaveException) -> JSONResponse:
    """FastAPI exception handler for domain exceptions."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, DocumentNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, UnsupportedFileTypeError):
        status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    elif isinstance(exc, (DocumentIngestionError, ExtractionError)):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
        },
    )
