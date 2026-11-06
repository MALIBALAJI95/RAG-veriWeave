"""Recursive character text chunker preserving page and document metadata."""

from typing import List, Optional
from backend.app.core.logging import get_logger
from backend.app.ingestion.loaders.base import RawDocumentPage
from backend.app.schemas.document import DocumentChunk

logger = get_logger(__name__)


class RecursiveCharacterChunker:
    """Splits raw document pages into overlapping semantic chunks using hierarchy of separators."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        separators: Optional[List[str]] = None,
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) must be smaller than chunk_size ({chunk_size})")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using the first separator that breaks it into smaller segments."""
        text = text.strip()
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        # Find best separator
        separator = separators[-1]
        next_separators: List[str] = []

        for idx, s in enumerate(separators):
            if s == "":
                separator = ""
                next_separators = []
                break
            if s in text:
                separator = s
                next_separators = separators[idx + 1 :]
                break

        # Split text by chosen separator
        if separator != "":
            splits = text.split(separator)
        else:
            # Character-level fallback
            splits = list(text)

        # Merge splits up to chunk_size with chunk_overlap
        chunks: List[str] = []
        current_doc: List[str] = []
        total_len = 0

        for s in splits:
            s_len = len(s) + (len(separator) if current_doc and separator else 0)
            if total_len + s_len > self.chunk_size:
                if current_doc:
                    doc = separator.join(current_doc).strip()
                    if doc:
                        chunks.append(doc)

                    # Keep overlap from the end of current_doc
                    overlap_doc: List[str] = []
                    overlap_len = 0
                    for elem in reversed(current_doc):
                        elem_len = len(elem) + (len(separator) if overlap_doc and separator else 0)
                        if overlap_len + elem_len <= self.chunk_overlap:
                            overlap_doc.insert(0, elem)
                            overlap_len += elem_len
                        else:
                            break
                    current_doc = overlap_doc
                    total_len = sum(len(x) for x in current_doc) + max(0, len(current_doc) - 1) * len(separator)

                if s_len > self.chunk_size:
                    # Recursively split oversized split
                    sub_splits = self._split_text(s, next_separators) if next_separators else [s[: self.chunk_size]]
                    chunks.extend(sub_splits)
                    continue

            current_doc.append(s)
            total_len += s_len

        if current_doc:
            doc = separator.join(current_doc).strip()
            if doc:
                chunks.append(doc)

        return chunks

    def chunk_pages(
        self,
        pages: List[RawDocumentPage],
        doc_id: str,
        filename: str,
    ) -> List[DocumentChunk]:
        """Chunk a list of document pages, preserving precise page number and character offsets."""
        chunks: List[DocumentChunk] = []
        global_chunk_index = 0

        for page in pages:
            raw_text = page.text.strip()
            if not raw_text:
                continue

            page_chunks = self._split_text(raw_text, self.separators)
            char_cursor = 0

            for chunk_text in page_chunks:
                chunk_clean = chunk_text.strip()
                if not chunk_clean:
                    continue

                # Locate character position in page text
                char_start = raw_text.find(chunk_clean, char_cursor)
                if char_start == -1:
                    char_start = char_cursor
                char_end = char_start + len(chunk_clean)
                char_cursor = max(0, char_start + len(chunk_clean) - self.chunk_overlap)

                # Token estimate (~1.3 tokens per whitespace-delimited word)
                token_estimate = int(len(chunk_clean.split()) * 1.3)

                chunk = DocumentChunk(
                    chunk_id=f"{doc_id}_c{global_chunk_index}",
                    doc_id=doc_id,
                    filename=filename,
                    page_number=page.page_number,
                    chunk_index=global_chunk_index,
                    text=chunk_clean,
                    char_start=char_start,
                    char_end=char_end,
                    token_count_estimate=token_estimate,
                    metadata={
                        **page.metadata,
                        "char_length": len(chunk_clean),
                    },
                )
                chunks.append(chunk)
                global_chunk_index += 1

        logger.info(
            f"Chunked document '{filename}': {len(pages)} pages -> {len(chunks)} chunks "
            f"(chunk_size={self.chunk_size}, overlap={self.chunk_overlap})"
        )
        return chunks
