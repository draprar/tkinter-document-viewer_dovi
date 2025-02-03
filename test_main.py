import fitz
import pytest
from unittest.mock import MagicMock
import tkinter as tk
from main import DocumentViewer

@pytest.fixture
def viewer():
    """Fixture to set up and tear down a DocumentViewer instance for testing."""
    root = tk.Tk()
    tk.Canvas(root)
    viewer_instance = DocumentViewer(root)
    yield viewer_instance
    root.destroy()

# File Handling & Loading
def test_load_invalid_file(viewer):
    viewer.load_document = MagicMock(side_effect=Exception("Unsupported file type"))
    with pytest.raises(Exception, match="Unsupported file type"):
        viewer.load_document("invalid.txt")
    with pytest.raises(Exception, match="Unsupported file type"):
        viewer.load_document("unsupported.docx")
    with pytest.raises(Exception, match="Unsupported file type"):
        viewer.load_document("random.exe")

# Navigation (Pages, Edge Cases)
def test_initial_page(viewer):
    assert viewer.current_page == 0

def test_prev_page_boundary(viewer):
    viewer.current_page = 0
    viewer.prev_page()
    assert viewer.current_page == 0

def test_next_page_boundary_pdf(viewer):
    viewer.doc_type = "pdf"
    viewer.doc = [fitz.open() for _ in range(5)]
    viewer.current_page = 4
    viewer.next_page()
    assert viewer.current_page == 4

def test_next_page_boundary_epub(viewer):
    viewer.doc_type = "epub"
    class MockEpubItem:
        """Mock class representing an EPUB item for testing navigation."""
        pass
    viewer.epub_items = [MockEpubItem() for _ in range(5)]
    viewer.doc = viewer.epub_items
    viewer.current_page = 4
    viewer.next_page()
    assert viewer.current_page == 4

# Search Functionality
def test_search_no_results(viewer):
    viewer.search_text = MagicMock(return_value=[])
    viewer.search_text()
    assert viewer.search_results == []

def test_search_results_found(viewer):
    viewer.search_results = [(10, 5), (20, 15), (30, 25)]
    viewer.current_match_index = 1
    viewer.next_match()
    assert viewer.current_page == 30

# Zooming
def test_zoom_limits(viewer):
    viewer.zoom_scale = 0.2
    viewer.zoom_out()
    assert viewer.zoom_scale == 0.2
    viewer.zoom_scale = 5.0
    viewer.zoom_in()
    assert viewer.zoom_scale > 5.0

# Fullscreen Toggle
def test_fullscreen_toggle(viewer):
    viewer.fullscreen = False
    viewer.toggle_fullscreen()
    assert viewer.fullscreen is True
    viewer.toggle_fullscreen()
    assert viewer.fullscreen is False

# Additional Test Cases
def test_reload_document(viewer):
    viewer.load_document = MagicMock()
    viewer.reload_document = MagicMock()
    viewer.reload_document()
    viewer.reload_document.assert_called_once()

def test_goto_valid_page(viewer):
    viewer.total_pages = 10
    viewer.goto_page = MagicMock()
    viewer.goto_page(5)
    viewer.goto_page.assert_called_with(5)

def test_goto_invalid_page(viewer):
    viewer.total_pages = 10
    viewer.goto_page = MagicMock()
    viewer.goto_page(-1)
    viewer.goto_page.assert_called_with(-1)
    viewer.goto_page(15)
    viewer.goto_page.assert_called_with(15)

def test_goto_non_numeric(viewer):
    viewer.total_pages = 10
    viewer.goto_page = MagicMock(side_effect=ValueError)
    with pytest.raises(ValueError):
        viewer.goto_page("abc")

def test_scroll_navigation(viewer):
    viewer.current_page = 2
    viewer.total_pages = 10
    viewer.scroll_navigation = MagicMock()
    viewer.scroll_navigation(event=MagicMock(delta=-120))
    viewer.scroll_navigation.assert_called()

def test_ctrl_scroll_zoom(viewer):
    viewer.zoom_factor = 1.0
    viewer.ctrl_scroll_zoom = MagicMock()
    event = MagicMock(state=4, delta=-120)
    viewer.ctrl_scroll_zoom(event)
    viewer.ctrl_scroll_zoom.assert_called_with(event)
