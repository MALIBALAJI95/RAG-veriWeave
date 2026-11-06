"""PDF document loader with page-by-page text extraction."""

from pathlib import Path
from typing import List
import pypdf
from backend.app.core.exceptions import ExtractionError
from backend.app.core.logging import get_logger
from backend.app.ingestion.loaders.base import BaseDocumentLoader, RawDocumentPage

logger = get_logger(__name__)


class PDFLoader(BaseDocumentLoader):
    """Extracts text page-by-page from PDF files using pypdf."""

    def load(self, file_path: Path) -> List[RawDocumentPage]:
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        pages: List[RawDocumentPage] = []
        try:
            reader = pypdf.PdfReader(str(file_path))
            total_pages = len(reader.pages)
            logger.info(f"Loading PDF: {file_path.name} ({total_pages} pages)")

            for idx, page in enumerate(reader.pages):
                page_num = idx + 1
                try:
                    text = page.extract_text() or ""
                    # Normalize excessive whitespace but preserve paragraph structure
                    text = text.strip()
                    if text:
                        pages.append(
                            RawDocumentPage(
                                page_number=page_num,
                                text=text,
                                metadata={
                                    "total_pages": total_pages,
                                    "source": file_path.name,
                                },
                            )
                        )
                except Exception as page_err:
                    logger.warning(f"Error extracting page {page_num} of {file_path.name}: {page_err}")

            if not pages:
                # If all pages were empty or scanned images without OCR
                logger.warning(f"PDF {file_path.name} yielded no extractable text.")
                pages.append(
                    RawDocumentPage(
                        page_number=1,
                        text="",
                        metadata={"total_pages": total_pages, "empty": True},
                    )
                )

            return pages
        except Exception as e:
            logger.error(f"Failed to read PDF {file_path}: {e}")
            raise ExtractionError(f"Failed to extract text from PDF {file_path.name}: {str(e)}")
