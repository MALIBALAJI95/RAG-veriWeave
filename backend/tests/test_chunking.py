"""Unit tests for recursive text chunking and metadata preservation."""

import pytest
from backend.app.ingestion.chunkers.recursive_chunker import RecursiveCharacterChunker
from backend.app.ingestion.loaders.base import RawDocumentPage


def test_chunker_basic():
    chunker = RecursiveCharacterChunker(chunk_size=100, chunk_overlap=20)
    text = (
        "Artificial Intelligence is evolving rapidly. "
        "Vector databases enable scalable semantic retrieval. "
        "Language models synthesize grounded answers."
    )
    pages = [RawDocumentPage(page_number=1, text=text)]
    chunks = chunker.chunk_pages(pages=pages, doc_id="doc_123", filename="test.txt")

    assert len(chunks) >= 1
    for idx, c in enumerate(chunks):
        assert c.doc_id == "doc_123"
        assert c.filename == "test.txt"
        assert c.page_number == 1
        assert c.chunk_index == idx
        assert c.chunk_id == f"doc_123_c{idx}"
        assert len(c.text) > 0


def test_chunker_multi_page_preserves_page_numbers():
    chunker = RecursiveCharacterChunker(chunk_size=150, chunk_overlap=30)
    pages = [
        RawDocumentPage(page_number=1, text="Page one discusses system setup and environment variables."),
        RawDocumentPage(page_number=2, text="Page two describes Qdrant persistence and indexing configurations."),
        RawDocumentPage(page_number=3, text="Page three covers generation prompts and citation extraction."),
    ]
    chunks = chunker.chunk_pages(pages=pages, doc_id="doc_456", filename="guide.pdf")

    assert len(chunks) == 3
    assert chunks[0].page_number == 1
    assert "Page one" in chunks[0].text
    assert chunks[1].page_number == 2
    assert "Page two" in chunks[1].text
    assert chunks[2].page_number == 3
    assert "Page three" in chunks[2].text


def test_chunker_invalid_overlap():
    with pytest.raises(ValueError):
        RecursiveCharacterChunker(chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError):
        RecursiveCharacterChunker(chunk_size=100, chunk_overlap=150)


def test_chunker_empty_pages():
    chunker = RecursiveCharacterChunker(chunk_size=200, chunk_overlap=40)
    pages = [
        RawDocumentPage(page_number=1, text="   "),
        RawDocumentPage(page_number=2, text=""),
    ]
    chunks = chunker.chunk_pages(pages=pages, doc_id="empty_doc", filename="empty.txt")
    assert len(chunks) == 0
