import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
from typing import Optional
import ttkbootstrap as ttk
from concurrent.futures import ThreadPoolExecutor
from document_backend import DocumentBackend
try:
    import fitz
except Exception:
    # PyMuPDF (fitz) may not be available in all environments (e.g., lightweight CI/test runners).
    # Defer errors to runtime when PDF functionality is used.
    fitz = None
from PIL import ImageTk
try:
    from tkhtmlview import HTMLLabel
except Exception:
    HTMLLabel = None
try:
    import mobi
except Exception:
    mobi = None
from logger import logger


class DocumentViewer:
    """
    A document viewer for PDF, EPUB, and MOBI files with navigation, zoom,
    search, and fullscreen functionality.

    Attributes:
        root: Tkinter root window
        current_page: Current page number (0-indexed)
        zoom_scale: Current zoom level (1.0 = 100%)
        fullscreen: Fullscreen mode flag
        doc: Loaded document object
        doc_type: Document type ('pdf', 'epub', or 'mobi')
        doc_path: Full path to the loaded document
        search_results: List of search match locations (page_num, rect)
        current_match_index: Current search match index
    """

    def __init__(self, root: tk.Tk, create_ui: bool = True) -> None:
        self.root = root
        self.create_ui = create_ui
        self.root.title("Document Viewer")
        self.root.geometry("800x600")
        self.current_page = 0
        self.zoom_scale = 1.0
        self.fullscreen = False
        self.doc = None
        self.doc_type = None
        self.doc_path = None
        self.search_results = []
        self.current_match_index = 0

        # UI creation is optional to allow headless testing (set create_ui=False)
        self.canvas = None
        # backend handles document operations
        self.backend = DocumentBackend()
        # executor for offloading rendering to background thread
        self._executor: Optional[ThreadPoolExecutor] = None
        if create_ui:
            self._executor = ThreadPoolExecutor(max_workers=1)
            self.canvas = tk.Canvas(self.root, bg="white")
            self.canvas.pack(fill=tk.BOTH, expand=True)

            self.create_widgets()
            self.bind_events()
        else:
            # Lightweight stubs for headless/testing mode to avoid UI dependencies
            class _Stub:
                def config(self, *args, **kwargs):
                    return None

                def pack(self, *args, **kwargs):
                    return None

                def bind(self, *args, **kwargs):
                    return None

                def get(self):
                    return ""

                def insert(self, *args, **kwargs):
                    return None

                def delete(self, *args, **kwargs):
                    return None

            self.match_label = _Stub()
            self.page_entry = _Stub()

    def load_document(self, file_path: str) -> None:
        """
        Load a document from the specified file path.

        Supports PDF, EPUB, and MOBI formats.

        Args:
            file_path: Full path to the document file

        Raises:
            ValueError: If file type is not supported
            Exception: If document cannot be opened (corrupted, invalid format)
        """
        try:
            logger.info(f"Loading document: {file_path}")
            # delegate to backend
            self.backend.load_document(file_path)
            self.doc_path = file_path
            self.doc_type = self.backend.doc_type
            # keep some compatibility fields used by tests
            if self.doc_type == 'pdf':
                self.doc = self.backend.doc
            else:
                self.epub_items = getattr(self.backend, 'epub_items', [])
                self.doc = self.epub_items

            self.current_page = 0
            self.zoom_scale = 1.0
            self.search_results = []
            self.current_match_index = 0
            # render first page (UI-only)
            if self.create_ui:
                self.display_page()
        except Exception as e:
            logger.error(f"Failed to load document: {e}")
            # keep UX: show messagebox if UI available
            if self.create_ui:
                messagebox.showerror("Error", f"Could not open document: {e}")
            else:
                raise

    def create_widgets(self) -> None:
        """Create and configure UI widgets (toolbar, buttons, controls)."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Previous", command=self.prev_page).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Next", command=self.next_page).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Search", command=self.search_text).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Full Screen", command=self.toggle_fullscreen).pack(side=tk.LEFT, padx=5, pady=5)

        self.page_entry = ttk.Entry(toolbar, width=10)
        self.page_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.page_entry.insert(0, "Go to page")  # Placeholder text
        self.page_entry.bind(
            "<FocusIn>",
            lambda e: (
                self.page_entry.delete(0, tk.END)
                if self.page_entry.get() == "Go to page"
                else None
            ),
        )
        self.page_entry.bind(
            "<FocusOut>",
            lambda e: (
                self.page_entry.insert(0, "Go to page")
                if not self.page_entry.get()
                else None
            ),
        )
        ttk.Button(toolbar, text="Go", command=self.goto_page).pack(side=tk.LEFT, padx=5, pady=5)

        self.match_label = ttk.Label(toolbar, text="")
        self.match_label.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Prev Match", command=self.prev_match).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Next Match", command=self.next_match).pack(side=tk.LEFT, padx=5, pady=5)

        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())

    def bind_events(self) -> None:
        """Bind keyboard and mouse events to handler functions."""
        self.root.bind("<Control-MouseWheel>", self.ctrl_scroll_zoom)
        self.canvas.bind("<MouseWheel>", self.scroll_navigation)

    def open_file(self) -> None:
        """Open file dialog and load selected document."""
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF Files", "*.pdf"), ("EPUB Files", "*.epub"), ("MOBI Files", "*.mobi")]
        )
        if file_path:
            self.load_document(file_path)

    def display_page(self) -> None:
        """Render and display the current page on canvas."""
        # guard for headless/testing mode
        if not self.create_ui or self.canvas is None:
            return

        # clear canvas
        try:
            self.canvas.delete("all")
        except Exception:
            pass

        if self.doc_type == 'pdf':
            if self.current_page >= len(self.doc) or self.doc[self.current_page] is None:
                return  # Prevent errors when page is None

            # render in background thread to avoid blocking UI
            if self._executor:
                future = self._executor.submit(self.backend.render_pdf_page, self.current_page, self.zoom_scale)

                def _on_done(fut):
                    try:
                        img = fut.result()
                    except Exception as e:
                        logger.error(f"Render failed: {e}")
                        return

                    def _show():
                        img_tk = ImageTk.PhotoImage(img)
                        canvas_width = self.canvas.winfo_width()
                        canvas_height = self.canvas.winfo_height()
                        img_x = (canvas_width - img.width) // 2
                        img_y = (canvas_height - img.height) // 2
                        try:
                            self.canvas.create_image(img_x, img_y, anchor="nw", image=img_tk)
                            self.canvas.image = img_tk
                            self.highlight_matches()
                        except Exception as e:
                            logger.exception(f"Failed to draw image on canvas: {e}")

                    try:
                        # schedule on main loop
                        self.root.after(0, _show)
                    except Exception:
                        # fallback: call directly
                        _show()

                future.add_done_callback(_on_done)
            else:
                # synchronous fallback
                img = self.backend.render_pdf_page(self.current_page, self.zoom_scale)
                img_tk = ImageTk.PhotoImage(img)
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                img_x = (canvas_width - img.width) // 2
                img_y = (canvas_height - img.height) // 2
                self.canvas.create_image(img_x, img_y, anchor="nw", image=img_tk)
                self.canvas.image = img_tk
                self.highlight_matches()

        elif self.doc_type == 'epub' or self.doc_type == 'mobi':
            if self.current_page >= len(self.epub_items) or self.epub_items[self.current_page] is None:
                return  # Prevent errors when page is None

            # Use HTMLLabel from tkhtmlview for better HTML rendering (if available)
            content = self.epub_items[self.current_page].get_body_content().decode("utf-8")
            if HTMLLabel is None:
                # fallback: show as plain text on the canvas
                try:
                    self.canvas.create_text(10, 10, anchor='nw', text=content)
                except Exception:
                    pass
            else:
                html_label = HTMLLabel(self.canvas, html=content)
                html_label.pack(fill=tk.BOTH, expand=True)

    def prev_page(self) -> None:
        """Navigate to the previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()

    def next_page(self) -> None:
        """Navigate to the next page."""
        if self.current_page < len(self.doc) - 1:
            self.current_page += 1
            self.display_page()

    def zoom_in(self) -> None:
        """Increase zoom level by 10%."""
        self.zoom_scale += 0.1
        self.display_page()

    def zoom_out(self) -> None:
        """Decrease zoom level by 10% (minimum 0.2)."""
        if self.zoom_scale > 0.2:
            self.zoom_scale -= 0.1
        self.display_page()

    def search_text(self) -> None:
        """Open search dialog and find text in document."""
        query = simpledialog.askstring("Search", "Enter text to search for:")
        if not query:
            logger.debug("Search cancelled by user")
            return

        self.search_results = []
        self.current_match_index = 0

        if self.doc_type == 'pdf':
            logger.info(f"Searching for '{query}' in PDF")
            try:
                self.search_results = self.backend.search_pdf(query)
            except Exception as e:
                logger.error(f"Search failed: {e}")
                self.search_results = []

            if self.search_results:
                logger.info(f"Found {len(self.search_results)} matches")
                self.current_page = self.search_results[0][0]
                self.display_page()
                self.update_match_label()
            else:
                logger.info(f"No matches found for '{query}'")
                messagebox.showinfo("Search", "Text not found")
        else:
            logger.warning("Search only supported for PDF files")
            messagebox.showinfo("Search", "Search is only supported for PDF files")

    def highlight_matches(self) -> None:
        """Highlight search matches on current PDF page."""
        if self.doc_type == 'pdf' and self.search_results:
            for page_num, rect in self.search_results:
                if page_num == self.current_page:
                    x0, y0, x1, y1 = rect
                    self.canvas.create_rectangle(x0, y0, x1, y1, outline="red", width=2)

    def prev_match(self) -> None:
        """Navigate to previous search match."""
        if self.search_results:
            self.current_match_index = (self.current_match_index - 1) % len(self.search_results)
            self.current_page = self.search_results[self.current_match_index][0]
            self.display_page()
            self.update_match_label()

    def next_match(self) -> None:
        """Navigate to next search match."""
        if self.search_results:
            self.current_match_index = (self.current_match_index + 1) % len(self.search_results)
            self.current_page = self.search_results[self.current_match_index][0]
            self.display_page()
            self.update_match_label()

    def update_match_label(self) -> None:
        """Update search match counter label."""
        if self.search_results:
            self.match_label.config(text=f"Match {self.current_match_index + 1} of {len(self.search_results)}")

    def ctrl_scroll_zoom(self, event) -> None:
        """Handle Ctrl+MouseWheel for zooming."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def scroll_navigation(self, event) -> None:
        """Handle MouseWheel for page navigation."""
        if not (event.state & 0x4):  # Check if Ctrl is NOT pressed
            if event.delta > 0:
                self.prev_page()
            else:
                self.next_page()

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self) -> None:
        """Exit fullscreen mode."""
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)

    def goto_page(self) -> None:
        """
        Navigate to a specific page number entered by the user.

        Validates input and shows appropriate warning messages.
        """
        page_str = self.page_entry.get().strip()

        # Check for empty input
        if not page_str or page_str == "Go to page":
            logger.warning("goto_page: Empty input")
            messagebox.showwarning("Invalid Input", "Please enter a valid page number.")
            return

        try:
            page_number = int(page_str)
            if self.doc is None:
                logger.error("goto_page: No document loaded")
                messagebox.showwarning("Error", "No document loaded.")
                return

            if 0 <= page_number - 1 < len(self.doc):
                self.current_page = page_number - 1
                logger.info(f"Navigated to page {page_number}")
                self.display_page()
            else:
                logger.warning(
                    f"goto_page: Page {page_number} out of range (max: {len(self.doc)})"
                )
                messagebox.showwarning("Invalid Page", "Page number out of range.")
        except ValueError:
            logger.error(f"goto_page: Invalid input: {page_str}")
            messagebox.showwarning("Invalid Input", "Please enter a valid page number.")


if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    viewer = DocumentViewer(root)
    root.mainloop()
