import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
import ebooklib
import ttkbootstrap as ttk
import fitz
from PIL import Image, ImageTk
from ebooklib import epub
from tkhtmlview import HTMLLabel

class DocumentViewer:
    """
    A document viewer for PDF and EPUB files with navigation, zoom, search, and fullscreen functionality.
    """
    def __init__(self, root):
        self.root = root
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

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()
        self.bind_events()

    def load_document(self, file_path):
        try:
            self.doc_path = file_path
            self.doc_type = file_path.split('.')[-1].lower()

            if self.doc_type == 'pdf':
                self.doc = fitz.open(self.doc_path)
            elif self.doc_type == 'epub':
                self.doc = epub.read_epub(self.doc_path)
                self.epub_items = list(self.doc.get_items_of_type(ebooklib.ITEM_DOCUMENT))
            else:
                raise ValueError("Unsupported file type")

            self.current_page = 0
            self.zoom_scale = 1.0
            self.search_results = []
            self.current_match_index = 0
            self.display_page()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open document: {e}")

    def create_widgets(self):
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
        self.page_entry.bind("<FocusIn>", lambda e: self.page_entry.delete(0, tk.END))
        self.page_entry.bind("<FocusOut>", lambda e: self.page_entry.insert(0, "Go to page") if not self.page_entry.get() else None)
        ttk.Button(toolbar, text="Go", command=self.goto_page).pack(side=tk.LEFT, padx=5, pady=5)

        self.match_label = ttk.Label(toolbar, text="")
        self.match_label.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Prev Match", command=self.prev_match).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(toolbar, text="Next Match", command=self.next_match).pack(side=tk.LEFT, padx=5, pady=5)

        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())

    def bind_events(self):
        self.root.bind("<Control-MouseWheel>", self.ctrl_scroll_zoom)
        self.canvas.bind("<MouseWheel>", self.scroll_navigation)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf"), ("EPUB Files", "*.epub")])
        if file_path:
            self.load_document(file_path)

    def display_page(self):
        self.canvas.delete("all")

        if self.doc_type == 'pdf':
            if self.current_page >= len(self.doc) or self.doc[self.current_page] is None:
                return  # Prevent errors when page is None

            page = self.doc[self.current_page]
            pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_scale, self.zoom_scale))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_tk = ImageTk.PhotoImage(img)

            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            img_x = (canvas_width - pix.width) // 2
            img_y = (canvas_height - pix.height) // 2
            self.canvas.create_image(img_x, img_y, anchor="nw", image=img_tk)
            self.canvas.image = img_tk

            self.highlight_matches()

        elif self.doc_type == 'epub':
            if self.current_page >= len(self.epub_items) or self.epub_items[self.current_page] is None:
                return  # Prevent errors when page is None

            content = self.epub_items[self.current_page].get_body_content().decode("utf-8")
            self.canvas.create_text(10, 10, anchor="nw", text=content, width=self.canvas.winfo_width())

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()

    def next_page(self):
        if self.current_page < len(self.doc) - 1:
            self.current_page += 1
            self.display_page()

    def zoom_in(self):
        self.zoom_scale += 0.1
        self.display_page()

    def zoom_out(self):
        if self.zoom_scale > 0.2:
            self.zoom_scale -= 0.1
        self.display_page()

    def search_text(self):
        query = simpledialog.askstring("Search", "Enter text to search for:")
        if not query:
            return

        self.search_results = []
        self.current_match_index = 0

        if self.doc_type == 'pdf':
            for page_num, page in enumerate(self.doc):
                matches = [(page_num, match) for match in page.search_for(query)]
                self.search_results.extend(matches)

            if self.search_results:
                self.current_page = self.search_results[0][0]
                self.display_page()
                self.update_match_label()
            else:
                messagebox.showinfo("Search", "Text not found")

    def highlight_matches(self):
        if self.doc_type == 'pdf' and self.search_results:
            for page_num, rect in self.search_results:
                if page_num == self.current_page:
                    x0, y0, x1, y1 = rect
                    self.canvas.create_rectangle(x0, y0, x1, y1, outline="red", width=2)

    def prev_match(self):
        if self.search_results:
            self.current_match_index = (self.current_match_index - 1) % len(self.search_results)
            self.current_page = self.search_results[self.current_match_index][0]
            self.display_page()
            self.update_match_label()

    def next_match(self):
        if self.search_results:
            self.current_match_index = (self.current_match_index + 1) % len(self.search_results)
            self.current_page = self.search_results[self.current_match_index][0]
            self.display_page()
            self.update_match_label()

    def update_match_label(self):
        if self.search_results:
            self.match_label.config(text=f"Match {self.current_match_index + 1} of {len(self.search_results)}")

    def ctrl_scroll_zoom(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def scroll_navigation(self, event):
        if not (event.state & 0x4):  # Check if Ctrl is NOT pressed
            if event.delta > 0:
                self.prev_page()
            else:
                self.next_page()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self):
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)

    def goto_page(self):
        try:
            page_number = int(self.page_entry.get())
            if 0 <= page_number - 1 < len(self.doc):
                self.current_page = page_number - 1
                self.display_page()
            else:
                messagebox.showwarning("Invalid Page", "Page number out of range.")
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid page number.")

if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    viewer = DocumentViewer(root)
    root.mainloop()