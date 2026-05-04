import logging
import ebooklib
from ebooklib import epub
from typing import Any, List, Tuple, Optional

try:
    import fitz

    if not hasattr(fitz, "open"):
        raise ImportError("Wrong 'fitz' package installed. " "Uninstall 'fitz' and install PyMuPDF.")

except Exception:
    fitz = None

try:
    import mobi
except Exception:
    mobi = None

from PIL import Image

logger = logging.getLogger("dovi.document_backend")


class DocumentBackend:
    """Backend handling document loading, rendering and searching.

    This class encapsulates document access so UI code can remain small and
    testable. Optional heavy dependencies (PyMuPDF / mobi) are loaded
    defensively; when missing, PDF/MOBI features raise ImportError with a
    clear message.
    """

    def __init__(self) -> None:
        self.doc: Any = None
        self.doc_type: Optional[str] = None
        self.doc_path: Optional[str] = None
        self.epub_items: List[Any] = []

    def load_document(self, file_path: str) -> None:
        """Load a document from disk.

        Supported types: pdf, epub, mobi. Raises ImportError when optional
        dependency is missing, ValueError for unsupported type, or IOError on
        underlying I/O errors.
        """
        self.doc_path = file_path
        self.doc_type = file_path.split(".")[-1].lower()

        if self.doc_type == "pdf":
            if fitz is None:
                logger.warning("PyMuPDF (fitz) not available: PDF support disabled")
                # Provide an actionable hint so logs are helpful to archivists/users
                raise ImportError(
                    "PyMuPDF (fitz) is required to open PDF files. "
                    "Install it into your environment: `pip install PyMuPDF`"
                )
            try:
                self.doc = fitz.open(self.doc_path)
            except Exception as exc:  # IOError / fitz-specific errors
                logger.exception("Failed to open PDF: %s", self.doc_path)
                raise IOError(f"Failed to open PDF: {exc}") from exc
        elif self.doc_type == "epub":
            try:
                self.doc = epub.read_epub(self.doc_path)
                self.epub_items = list(self.doc.get_items_of_type(ebooklib.ITEM_DOCUMENT))
            except Exception as exc:
                logger.exception("Failed to read EPUB: %s", self.doc_path)
                raise IOError(f"Failed to read EPUB: {exc}") from exc
        elif self.doc_type == "mobi":
            if mobi is None:
                logger.warning("mobi package not available: MOBI support disabled")
                raise ImportError("mobi package is required to open MOBI files. " "Install it with: pip install mobi")

            try:
                # Extract MOBI contents to temporary folder
                temp_dir, extracted_file = mobi.extract(self.doc_path)

                logger.info("MOBI extracted to: %s", extracted_file)

                # Many MOBI files contain extracted HTML/OPF files
                with open(extracted_file, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read()

                self.doc = content
                self.epub_items = [content]

            except Exception as exc:
                logger.exception("Failed to load MOBI: %s", self.doc_path)
                raise IOError(f"Failed to load MOBI: {exc}") from exc
        else:
            raise ValueError("Unsupported file type")

    def page_count(self) -> int:
        """Return number of pages/items for the currently loaded document."""
        if self.doc_type == "pdf" and self.doc is not None:
            return len(self.doc)
        if self.doc_type in ("epub", "mobi"):
            return len(self.epub_items)
        return 0

    def render_pdf_page(self, page_index: int, zoom: float = 1.0) -> Image.Image:
        """Render a PDF page to a PIL.Image.

        Raises ImportError if PyMuPDF is not installed, ValueError/IndexError if
        the document is not a PDF or the page index is out of range, and
        RuntimeError on rendering failures.
        """
        if fitz is None:
            logger.error("Attempt to render PDF but PyMuPDF is not installed")
            raise ImportError("PyMuPDF (fitz) not installed")
        if self.doc is None or self.doc_type != "pdf":
            raise ValueError("No PDF document loaded")

        total = len(self.doc)
        if page_index < 0 or page_index >= total:
            raise IndexError(f"page_index {page_index} out of range (0..{total-1})")

        try:
            page = self.doc[page_index]
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            return img
        except Exception as exc:
            logger.exception("Failed to render PDF page %s", page_index)
            raise RuntimeError(f"Failed to render page {page_index}: {exc}") from exc

    def get_epub_content(self, index: int) -> str:
        """
        Return HTML/text content for EPUB or MOBI.
        """
        if not self.epub_items:
            raise ValueError("No EPUB/MOBI content available")

        if index < 0 or index >= len(self.epub_items):
            raise IndexError("Content index out of range")

        item = self.epub_items[index]

        try:
            if isinstance(item, str):
                return item

            content = item.get_body_content()

            if isinstance(content, bytes):
                return content.decode("utf-8")

            return str(content)

        except Exception as exc:
            logger.exception("Failed to extract content")
            raise ValueError(f"Failed to extract content: {exc}") from exc

    def search_pdf(self, query: str) -> List[Tuple[int, Tuple[float, float, float, float]]]:
        """Search text in PDF pages and return list of (page_index, rect) tuples.

        Rects are returned as plain tuples: (x0, y0, x1, y1).
        """
        results: List[Tuple[int, Tuple[float, float, float, float]]] = []
        if self.doc_type != "pdf" or self.doc is None:
            return results
        for page_num, page in enumerate(self.doc):
            try:
                matches = page.search_for(query)
            except Exception as exc:
                # If search isn't supported on a page, log and skip it
                logger.warning("Search failed on page %s, skipping: %s", page_num, exc)
                continue
            for m in matches:
                try:
                    rect = (float(m.x0), float(m.y0), float(m.x1), float(m.y1))
                except Exception:
                    # Fallback: try to convert to tuple
                    rect = tuple(m)  # type: ignore
                results.append((page_num, rect))
        return results