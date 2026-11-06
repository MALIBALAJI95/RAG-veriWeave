"""Core system modules: configuration, logging, exceptions."""

from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import (
    VeriWeaveException,
    DocumentIngestionError,
    UnsupportedFileTypeError,
    ExtractionError,
    VectorStorageError,
    EmbeddingError,
    GenerationError,
    DocumentNotFoundError,
)
from backend.app.core.logging import setup_logging, get_logger

__all__ = [
    "Settings",
    "get_settings",
    "VeriWeaveException",
    "DocumentIngestionError",
    "UnsupportedFileTypeError",
    "ExtractionError",
    "VectorStorageError",
    "EmbeddingError",
    "GenerationError",
    "DocumentNotFoundError",
    "setup_logging",
    "get_logger",
]
