"""Document loader exports."""

from backend.app.ingestion.loaders.base import BaseDocumentLoader, RawDocumentPage
from backend.app.ingestion.loaders.docx_loader import DocxLoader
from backend.app.ingestion.loaders.factory import get_loader_for_file
from backend.app.ingestion.loaders.pdf_loader import PDFLoader
from backend.app.ingestion.loaders.txt_loader import TxtLoader

__all__ = [
    "BaseDocumentLoader",
    "RawDocumentPage",
    "PDFLoader",
    "DocxLoader",
    "TxtLoader",
    "get_loader_for_file",
]
