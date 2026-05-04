import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from typing import List, Tuple, Any

import ttkbootstrap as ttk
from PIL import ImageTk

try:
    from tkhtmlview import HTMLLabel
except Exception:
    HTMLLabel = None

from document_backend import DocumentBackend
from logger import logger


class DocumentViewer:
    """
    GUI application for viewing PDF, EPUB, and MOBI documents.

    Handles:
    - document loading
    - page navigation
    - zoom controls
    - text searching
    - fullscreen mode
    - rendering content

    Business logic for document processing is delegated
    to DocumentBackend.
    """

    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize application window and viewer state.

        Args:
            root: Main Tkinter window.
        """
        self.root = root
        self.root.title("Document Viewer")
        self.root.geometry("800x600")

        self.backend = DocumentBackend()

        self.current_page: int = 0
        self.zoom_scale: float = 1.0
        self.fullscreen: bool = False

        self.search_results: List[Tuple[int, Any]] = []
        self.current_match_index: int = 0

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()
        self.bind_events()

    def create_widgets(self) -> None:
        """
        Create toolbar buttons and page controls.
        """
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        buttons = [
            ("Open", self.open_file),
            ("Prev", self.prev_page),
            ("Next", self.next_page),
            ("Zoom In", self.zoom_in),
            ("Zoom Out", self.zoom_out),
            ("Search", self.search_text),
            ("Prev Match", self.prev_match),
            ("Next Match", self.next_match),
            ("Fullscreen", self.toggle_fullscreen),
        ]

        for text, command in buttons:
            ttk.Button(toolbar, text=text, command=command).pack(side=tk.LEFT)

        self.page_entry = ttk.Entry(toolbar, width=10)
        self.page_entry.pack(side=tk.LEFT)

        ttk.Button(toolbar, text="Go", command=self.goto_page).pack(side=tk.LEFT)

    def bind_events(self) -> None:
        """
        Bind keyboard/mouse events.
        """
        self.canvas.bind("<MouseWheel>", self.scroll_navigation)

        self.canvas.bind("<Configure>", lambda event: self.display_page())

        self.root.bind("<Escape>", lambda event: self.exit_fullscreen())

    def open_file(self) -> None:
        """
        Open file dialog and load selected document.
        """
        file_path = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf *.epub *.mobi")])

        if not file_path:
            logger.info("File selection cancelled.")
            return

        try:
            self.backend.load_document(file_path)

            self.current_page = 0
            self.zoom_scale = 1.0
            self.search_results = []
            self.current_match_index = 0

            logger.info("Loaded document: %s", file_path)

            self.display_page()

        except Exception as error:
            logger.exception("Failed loading file")
            messagebox.showerror("Error", str(error))

    def display_page(self) -> None:
        """
        Render current document page/content.
        """
        self.canvas.delete("all")

        # Remove previously embedded widgets
        for widget in self.canvas.winfo_children():
            widget.destroy()

        try:
            if self.backend.doc_type == "pdf":
                self._display_pdf_page()

            elif self.backend.doc_type in ("epub", "mobi"):
                self._display_ebook_content()

        except Exception as error:
            logger.exception("Display error")
            messagebox.showerror("Error", str(error))

    def _display_pdf_page(self) -> None:
        """
        Render PDF page centered in canvas, then overlay search highlights.
        """
        image = self.backend.render_pdf_page(self.current_page, self.zoom_scale)

        image_tk = ImageTk.PhotoImage(image)

        self.canvas.update_idletasks()

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        center_x = canvas_width // 2
        center_y = canvas_height // 2

        self.canvas.create_image(center_x, center_y, anchor="center", image=image_tk)

        # Prevent image from being garbage collected (Tkinter limitation)
        self.canvas.image = image_tk

        self._draw_search_highlights(center_x, center_y, image.width, image.height)

    def _draw_search_highlights(self, center_x: int, center_y: int, img_w: int, img_h: int) -> None:
        """
        Overlay semi-transparent highlight rectangles for search matches on the current page.

        The active match (current_match_index) is drawn in orange; all other
        matches on the same page are drawn in yellow.

        Args:
            center_x: Horizontal center of the rendered image on the canvas.
            center_y: Vertical center of the rendered image on the canvas.
            img_w: Width of the rendered image in pixels.
            img_h: Height of the rendered image in pixels.
        """
        if not self.search_results:
            return

        # Top-left corner of the image in canvas coordinates
        img_origin_x = center_x - img_w // 2
        img_origin_y = center_y - img_h // 2

        for match_idx, (page_num, rect) in enumerate(self.search_results):
            if page_num != self.current_page:
                continue

            x0, y0, x1, y1 = rect

            # PDF rect coords are in points; scale to pixel coords via zoom
            cx0 = img_origin_x + x0 * self.zoom_scale
            cy0 = img_origin_y + y0 * self.zoom_scale
            cx1 = img_origin_x + x1 * self.zoom_scale
            cy1 = img_origin_y + y1 * self.zoom_scale

            is_active = match_idx == self.current_match_index
            color = "#FF8C00" if is_active else "#FFD700"
            stipple = "gray50" if is_active else "gray25"

            self.canvas.create_rectangle(
                cx0,
                cy0,
                cx1,
                cy1,
                fill=color,
                outline=color,
                stipple=stipple,
                width=2,
            )

    def _display_ebook_content(self) -> None:
        """
        Render EPUB/MOBI HTML content centered in canvas.
        """
        if HTMLLabel is None:
            raise ImportError("tkhtmlview is required " "for EPUB/MOBI rendering.")

        content = self.backend.get_epub_content(self.current_page)

        self.canvas.update_idletasks()

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        html_label = HTMLLabel(self.canvas, html=content, width=80)

        self.canvas.create_window(canvas_width // 2, canvas_height // 2, anchor="center", window=html_label)

    def prev_page(self) -> None:
        """
        Navigate to previous page.
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()

    def next_page(self) -> None:
        """
        Navigate to next page.
        """
        if self.current_page < (self.backend.page_count() - 1):
            self.current_page += 1
            self.display_page()

    def zoom_in(self) -> None:
        """
        Increase zoom level.
        """
        self.zoom_scale += 0.1
        self.display_page()

    def zoom_out(self) -> None:
        """
        Decrease zoom level.
        """
        if self.zoom_scale > 0.2:
            self.zoom_scale -= 0.1
            self.display_page()

    def search_text(self) -> None:
        """
        Search text inside PDF documents and jump to first match.
        """
        query = simpledialog.askstring("Search", "Enter text:")

        if not query:
            return

        self.search_results = self.backend.search_pdf(query)

        if self.search_results:
            self.current_match_index = 0
            self.current_page = self.search_results[0][0]
            self.display_page()
        else:
            messagebox.showinfo("Search", "No matches found")

    def prev_match(self) -> None:
        """
        Jump to the previous search result match.
        """
        if not self.search_results:
            messagebox.showinfo("Search", "No search results. Use Search first.")
            return

        self.current_match_index = (self.current_match_index - 1) % len(self.search_results)
        self.current_page = self.search_results[self.current_match_index][0]
        self.display_page()

    def next_match(self) -> None:
        """
        Jump to the next search result match.
        """
        if not self.search_results:
            messagebox.showinfo("Search", "No search results. Use Search first.")
            return

        self.current_match_index = (self.current_match_index + 1) % len(self.search_results)
        self.current_page = self.search_results[self.current_match_index][0]
        self.display_page()

    def goto_page(self) -> None:
        """
        Navigate to a user-specified page.
        """
        try:
            page = int(self.page_entry.get()) - 1

            if 0 <= page < self.backend.page_count():
                self.current_page = page
                self.display_page()
            else:
                messagebox.showwarning("Warning", "Page out of range")

        except ValueError:
            messagebox.showwarning("Warning", "Invalid page number")

    def scroll_navigation(self, event: tk.Event) -> None:
        """
        Navigate pages using mouse wheel.

        Args:
            event: Mouse wheel event.
        """
        if event.delta > 0:
            self.prev_page()
        else:
            self.next_page()

    def toggle_fullscreen(self) -> None:
        """
        Toggle fullscreen mode.
        """
        self.fullscreen = not self.fullscreen

        self.root.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self) -> None:
        """
        Exit fullscreen mode.
        """
        self.fullscreen = False

        self.root.attributes("-fullscreen", False)


if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    app = DocumentViewer(root)
    root.mainloop()
