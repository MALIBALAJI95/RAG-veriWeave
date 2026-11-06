"""DOCX document loader with section and paragraph extraction."""

from pathlib import Path
from typing import List
import docx
from backend.app.core.exceptions import ExtractionError
from backend.app.core.logging import get_logger
from backend.app.ingestion.loaders.base import BaseDocumentLoader, RawDocumentPage

logger = get_logger(__name__)


class DocxLoader(BaseDocumentLoader):
    """Extracts text from DOCX files, grouping paragraphs into logical pages/sections."""

    # Approximate page size in characters for word processing docs without layout engine
    APPROX_PAGE_CHAR_LIMIT = 2500

    def load(self, file_path: Path) -> List[RawDocumentPage]:
        if not file_path.exists():
            raise FileNotFoundError(f"DOCX file not found: {file_path}")

        try:
            doc = docx.Document(str(file_path))
            pages: List[RawDocumentPage] = []
            current_page_text: List[str] = []
            current_page_num = 1
            current_char_count = 0

            # Extract paragraphs
            for p in doc.paragraphs:
                p_text = p.text.strip()
                if not p_text:
                    continue

                p_len = len(p_text)
                if current_char_count + p_len > self.APPROX_PAGE_CHAR_LIMIT and current_page_text:
                    # Flush accumulated page
                    pages.append(
                        RawDocumentPage(
                            page_number=current_page_num,
                            text="\n\n".join(current_page_text),
                            metadata={"source": file_path.name, "section_type": "paragraphs"},
                        )
                    )
                    current_page_num += 1
                    current_page_text = [p_text]
                    current_char_count = p_len
                else:
                    current_page_text.append(p_text)
                    current_char_count += p_len

            # Extract tables as formatted text
            for table in doc.tables:
                table_lines = []
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    table_lines.append(" | ".join(row_cells))
                if table_lines:
                    table_text = "\n".join(table_lines)
                    current_page_text.append(table_text)

            # Flush final page
            if current_page_text:
                pages.append(
                    RawDocumentPage(
                        page_number=current_page_num,
                        text="\n\n".join(current_page_text),
                        metadata={"source": file_path.name},
                    )
                )

            if not pages:
                pages.append(
                    RawDocumentPage(
                        page_number=1,
                        text="",
                        metadata={"source": file_path.name, "empty": True},
                    )
                )

            logger.info(f"Loaded DOCX: {file_path.name} ({len(pages)} logical pages)")
            return pages
        except Exception as e:
            logger.error(f"Failed to read DOCX {file_path}: {e}")
            raise ExtractionError(f"Failed to extract text from DOCX {file_path.name}: {str(e)}")
