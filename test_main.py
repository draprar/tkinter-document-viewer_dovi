import fitz
import pytest
from unittest.mock import MagicMock
import tkinter as tk
from main import DocumentViewer

@pytest.fixture
def viewer():
    root = tk.Tk()  # Create the main application window
    tk.Canvas(root)
    viewer_instance = DocumentViewer(root)  # Pass the root, not canvas
    yield viewer_instance
    root.destroy()  # Clean up the Tkinter window after the test

# File Handling & Loading
def test_load_invalid_file(viewer):
    viewer.load_document = MagicMock(side_effect=Exception("Unsupported file type"))
    with pytest.raises(Exception, match="Unsupported file type"):
        viewer.load_document("invalid.txt")

# Navigation (Pages, Edge Cases)
def test_initial_page(viewer):
    assert viewer.current_page == 0

def test_prev_page_boundary(viewer):
    viewer.current_page = 0
    viewer.prev_page()
    assert viewer.current_page == 0  # Should not go below 0

def test_next_page_boundary_pdf(viewer):
    viewer.doc_type = "pdf"
    viewer.doc = [fitz.open() for _ in range(5)]  # Mock PDF pages
    viewer.current_page = 4
    viewer.next_page()
    assert viewer.current_page == 4  # Should not go beyond last page


def test_next_page_boundary_epub(viewer):
    viewer.doc_type = "epub"

    class MockEpubItem:
        pass

    viewer.epub_items = [MockEpubItem() for _ in range(5)]
    viewer.doc = viewer.epub_items  # Ensure doc is not None
    viewer.current_page = 4

    viewer.next_page()  # Should not raise an error
    assert viewer.current_page == 4  # Should remain at last page

# Search Functionality
def test_search_no_results(viewer):
    viewer.search_text = MagicMock(return_value=[])
    viewer.search_text()
    assert viewer.search_results == []

def test_search_results_found(viewer):
    viewer.search_results = [(10, 5), (20, 15), (30, 25)]  # Mocked results
    viewer.current_match_index = 1
    viewer.next_match()
    assert viewer.current_page == 30  # Should navigate to the next search match

# Zooming
def test_zoom_limits(viewer):
    viewer.zoom_scale = 0.2
    viewer.zoom_out()
    assert viewer.zoom_scale == 0.2  # Shouldn't go below 0.2
    viewer.zoom_scale = 5.0
    viewer.zoom_in()
    assert viewer.zoom_scale > 5.0  # Should zoom in properly

# Fullscreen Toggle
def test_fullscreen_toggle(viewer):
    viewer.fullscreen = False
    viewer.toggle_fullscreen()
    assert viewer.fullscreen is True
    viewer.toggle_fullscreen()
    assert viewer.fullscreen is False
