import ebooklib
import fitz
import ttkbootstrap as ttk
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
from PIL import Image, ImageTk
from ebooklib import epub
from tkhtmlview import HTMLLabel


class DocumentViewer:
    def __init__(self, root):
        self.epub_items = None
        self.root = root
        self.root.title("Document Viewer")
        self.root.geometry("800x600")
        self.current_page = 0
        self.zoom_scale = 1.0
        self.fullscreen = False
        self.doc = None
        self.doc_type = None
        self.doc_path = None

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()

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

        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf"), ("EPUB Files", "*.epub")])
        if file_path:
            self.load_document(file_path)

    def display_page(self):
        self.canvas.delete("all")

        if self.doc_type == 'pdf':
            page = self.doc[self.current_page]
            pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_scale, self.zoom_scale))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_tk = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor="nw", image=img_tk)
            self.canvas.image = img_tk
        elif self.doc_type == 'epub':
            content = self.epub_items[self.current_page].get_body_content().decode("utf-8")
            label = HTMLLabel(self.canvas, html=content)
            label.pack(fill=tk.BOTH, expand=True)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()

    def next_page(self):
        if self.doc_type == 'pdf' and self.current_page < len(self.doc) - 1:
            self.current_page += 1
        elif self.doc_type == 'epub' and self.current_page < len(self.epub_items) - 1:
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

        if self.doc_type == 'pdf':
            for i in range(len(self.doc)):
                if query.lower() in self.doc[i].get_text().lower():
                    self.current_page = i
                    self.display_page()
                    return
            messagebox.showinfo("Search", "Text not found")

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self):
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)

if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    viewer = DocumentViewer(root)
    root.mainloop()
