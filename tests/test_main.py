import pytest
from unittest.mock import MagicMock, patch

from main import DocumentViewer


@pytest.fixture
def mock_root():
    root = MagicMock()
    root.title = MagicMock()
    root.geometry = MagicMock()
    root.bind = MagicMock()
    root.attributes = MagicMock()
    return root


@pytest.fixture
def viewer(mock_root):
    with patch("main.tk.Canvas") as mock_canvas:
        canvas_instance = MagicMock()
        mock_canvas.return_value = canvas_instance

        with patch.object(DocumentViewer, "create_widgets"), \
             patch.object(DocumentViewer, "bind_events"):

            viewer = DocumentViewer(mock_root)
            viewer.canvas = canvas_instance
            viewer.backend = MagicMock()

            return viewer


def test_initial_page(viewer):
    assert viewer.current_page == 0


def test_prev_page_boundary(viewer):
    viewer.current_page = 0
    viewer.prev_page()

    assert viewer.current_page == 0


def test_next_page_boundary(viewer):
    viewer.current_page = 4
    viewer.backend.page_count.return_value = 5

    viewer.next_page()

    assert viewer.current_page == 4


def test_next_page_success(viewer):
    viewer.current_page = 2
    viewer.backend.page_count.return_value = 10

    viewer.next_page()

    assert viewer.current_page == 3


def test_zoom_in(viewer):
    initial = viewer.zoom_scale

    viewer.zoom_in()

    assert viewer.zoom_scale > initial


def test_zoom_out_limit(viewer):
    viewer.zoom_scale = 0.2

    viewer.zoom_out()

    assert viewer.zoom_scale == 0.2


def test_scroll_navigation_next(viewer):
    event = MagicMock()
    event.delta = -120

    viewer.next_page = MagicMock()

    viewer.scroll_navigation(event)

    viewer.next_page.assert_called_once()


def test_scroll_navigation_prev(viewer):
    event = MagicMock()
    event.delta = 120

    viewer.prev_page = MagicMock()

    viewer.scroll_navigation(event)

    viewer.prev_page.assert_called_once()


def test_search_results_found(viewer):
    viewer.backend.search_pdf.return_value = [(2, (1, 2, 3, 4))]

    with patch("main.simpledialog.askstring", return_value="test"):
        viewer.display_page = MagicMock()

        viewer.search_text()

        assert viewer.current_page == 2
        viewer.display_page.assert_called_once()


def test_search_no_results(viewer):
    viewer.backend.search_pdf.return_value = []

    with patch("main.simpledialog.askstring", return_value="test"):
        with patch("main.messagebox.showinfo") as mock_info:
            viewer.search_text()

            mock_info.assert_called_once()


def test_toggle_fullscreen(viewer):
    viewer.fullscreen = False

    viewer.toggle_fullscreen()

    assert viewer.fullscreen is True
