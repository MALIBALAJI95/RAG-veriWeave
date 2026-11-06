"""Loader factory for document formats."""

from pathlib import Path
from backend.app.core.exceptions import UnsupportedFileTypeError
from backend.app.ingestion.loaders.base import BaseDocumentLoader
from backend.app.ingestion.loaders.docx_loader import DocxLoader
from backend.app.ingestion.loaders.pdf_loader import PDFLoader
from backend.app.ingestion.loaders.txt_loader import TxtLoader


SUPPORTED_EXTENSIONS = {
    ".pdf": PDFLoader,
    ".docx": DocxLoader,
    ".doc": DocxLoader,
    ".txt": TxtLoader,
    ".md": TxtLoader,
    ".markdown": TxtLoader,
}


def get_loader_for_file(file_path: Path) -> BaseDocumentLoader:
    """Resolve and instantiate the proper document loader based on file extension."""
    ext = file_path.suffix.lower()
    loader_cls = SUPPORTED_EXTENSIONS.get(ext)
    if not loader_cls:
        raise UnsupportedFileTypeError(
            f"File format '{ext}' is not supported. Supported extensions: {list(SUPPORTED_EXTENSIONS.keys())}"
        )
    return loader_cls()
