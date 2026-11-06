"""Unit tests for document loaders and extraction."""

from pathlib import Path
import pytest
from backend.app.core.exceptions import ExtractionError, UnsupportedFileTypeError
from backend.app.ingestion.loaders.docx_loader import DocxLoader
from backend.app.ingestion.loaders.factory import get_loader_for_file
from backend.app.ingestion.loaders.pdf_loader import PDFLoader
from backend.app.ingestion.loaders.txt_loader import TxtLoader


def test_pdf_loader_multi_page(sample_pdf_path: Path):
    loader = PDFLoader()
    pages = loader.load(sample_pdf_path)

    assert len(pages) == 2, f"Expected 2 pages, got {len(pages)}"
    assert pages[0].page_number == 1
    assert "Page 1" in pages[0].text
    assert "Retrieval-Augmented Generation" in pages[0].text
    assert pages[1].page_number == 2
    assert "Page 2" in pages[1].text
    assert "Qdrant" in pages[1].text


def test_docx_loader(sample_docx_path: Path):
    loader = DocxLoader()
    pages = loader.load(sample_docx_path)

    assert len(pages) >= 1
    full_text = " ".join(p.text for p in pages)
    assert "Dense Retrieval" in full_text
    assert "BM25" in full_text
    # Verify table content was extracted
    assert "Exact keyword mismatch" in full_text


def test_txt_loader(sample_txt_path: Path):
    loader = TxtLoader()
    pages = loader.load(sample_txt_path)

    assert len(pages) >= 1
    assert pages[0].page_number == 1
    assert "Autonomous agents are computational systems" in pages[0].text


def test_loader_factory(sample_pdf_path: Path, sample_docx_path: Path, sample_txt_path: Path):
    assert isinstance(get_loader_for_file(sample_pdf_path), PDFLoader)
    assert isinstance(get_loader_for_file(sample_docx_path), DocxLoader)
    assert isinstance(get_loader_for_file(sample_txt_path), TxtLoader)


def test_loader_factory_unsupported():
    with pytest.raises(UnsupportedFileTypeError):
        get_loader_for_file(Path("archive.zip"))

    with pytest.raises(UnsupportedFileTypeError):
        get_loader_for_file(Path("binary.exe"))


def test_pdf_loader_missing_file(temp_dir: Path):
    loader = PDFLoader()
    with pytest.raises(FileNotFoundError):
        loader.load(temp_dir / "non_existent.pdf")
