import pytest
from unittest.mock import MagicMock, patch

from document_backend import DocumentBackend


@pytest.fixture
def backend():
    return DocumentBackend()


def test_pdf_type_detection(backend):
    with patch("document_backend.fitz.open") as mock_open:
        backend.load_document("test.pdf")

        assert backend.doc_type == "pdf"
        mock_open.assert_called_once()


def test_unsupported_file_type(backend):
    with pytest.raises(ValueError):
        backend.load_document("test.docx")


def test_page_count_pdf(backend):
    backend.doc_type = "pdf"
    backend.doc = [1, 2, 3]

    assert backend.page_count() == 3


def test_page_count_epub(backend):
    backend.doc_type = "epub"
    backend.epub_items = [1, 2]

    assert backend.page_count() == 2


def test_search_pdf_returns_results(backend):
    mock_page = MagicMock()
    mock_rect = MagicMock(
        x0=1,
        y0=2,
        x1=3,
        y1=4
    )

    mock_page.search_for.return_value = [mock_rect]

    backend.doc_type = "pdf"
    backend.doc = [mock_page]

    results = backend.search_pdf("hello")

    assert len(results) == 1
    assert results[0][0] == 0


def test_search_pdf_no_document(backend):
    backend.doc = None
    backend.doc_type = None

    results = backend.search_pdf("hello")

    assert results == []