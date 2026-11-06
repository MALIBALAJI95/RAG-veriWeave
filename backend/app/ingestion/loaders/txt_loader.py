"""TXT and Markdown document loader with page partitioning."""

from pathlib import Path
from typing import List
from backend.app.core.exceptions import ExtractionError
from backend.app.core.logging import get_logger
from backend.app.ingestion.loaders.base import BaseDocumentLoader, RawDocumentPage

logger = get_logger(__name__)


class TxtLoader(BaseDocumentLoader):
    """Extracts text from plain text and markdown documents."""

    APPROX_PAGE_CHAR_LIMIT = 2500

    def load(self, file_path: Path) -> List[RawDocumentPage]:
        if not file_path.exists():
            raise FileNotFoundError(f"Text file not found: {file_path}")

        try:
            # Try UTF-8 first, fallback to latin-1
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = file_path.read_text(encoding="latin-1")

            content = content.strip()
            if not content:
                return [RawDocumentPage(page_number=1, text="", metadata={"source": file_path.name, "empty": True})]

            # Check if there are form feed characters (\x0c) representing physical page breaks
            if "\x0c" in content:
                raw_pages = content.split("\x0c")
                pages = [
                    RawDocumentPage(
                        page_number=idx + 1,
                        text=p.strip(),
                        metadata={"source": file_path.name},
                    )
                    for idx, p in enumerate(raw_pages)
                    if p.strip()
                ]
                return pages if pages else [RawDocumentPage(page_number=1, text="", metadata={"source": file_path.name})]

            # If content exceeds approx page length, divide by paragraph boundaries
            paragraphs = content.split("\n\n")
            pages: List[RawDocumentPage] = []
            curr_text: List[str] = []
            curr_len = 0
            page_num = 1

            for p in paragraphs:
                p_clean = p.strip()
                if not p_clean:
                    continue
                if curr_len + len(p_clean) > self.APPROX_PAGE_CHAR_LIMIT and curr_text:
                    pages.append(
                        RawDocumentPage(
                            page_number=page_num,
                            text="\n\n".join(curr_text),
                            metadata={"source": file_path.name},
                        )
                    )
                    page_num += 1
                    curr_text = [p_clean]
                    curr_len = len(p_clean)
                else:
                    curr_text.append(p_clean)
                    curr_len += len(p_clean)

            if curr_text:
                pages.append(
                    RawDocumentPage(
                        page_number=page_num,
                        text="\n\n".join(curr_text),
                        metadata={"source": file_path.name},
                    )
                )

            logger.info(f"Loaded Text: {file_path.name} ({len(pages)} logical pages)")
            return pages
        except Exception as e:
            logger.error(f"Failed to read TXT {file_path}: {e}")
            raise ExtractionError(f"Failed to extract text from {file_path.name}: {str(e)}")
