import io

import pymupdf
import pytesseract
from PIL import Image

from app.parsing.base import DocumentParser
from app.parsing.errors import DocumentParseError
from app.parsing.models import ParsedDocument, ParsedPage

# Rendering DPI used only for OCR fallback pages (scanned PDFs with no
# extractable text layer). 200 DPI is the standard tesseract-accuracy
# sweet spot -- higher costs much more time for little accuracy gain.
OCR_RENDER_DPI = 200


def _ocr_page(page: "pymupdf.Page") -> str:
    """Render a PDF page to an image and OCR it.

    Used only as a fallback when a page has no embedded text layer
    (i.e. it's a scan/photo, not real text). Never raises: if
    tesseract itself is unavailable on the host, this returns an empty
    string rather than failing the whole document parse -- a missing
    OCR page still leaves every OTHER page usable.
    """

    try:
        pixmap = page.get_pixmap(dpi=OCR_RENDER_DPI)
        image = Image.open(io.BytesIO(pixmap.tobytes("png")))

        return pytesseract.image_to_string(image)
    except Exception:
        return ""


class PdfParser(DocumentParser):
    """Parser for PDF documents.

    Extracts the embedded text layer per page. When a page has no
    extractable text (a scanned/photographed page with no text layer
    at all), it is rendered to an image and OCR'd via tesseract as a
    fallback -- this is what makes scanned contracts/invoices usable
    by the rest of the pipeline instead of silently producing an empty
    page.
    """

    SUPPORTED_CONTENT_TYPES = {
        "application/pdf",
    }

    SUPPORTED_EXTENSIONS = {
        ".pdf",
    }

    def supports(self, content_type: str, filename: str) -> bool:
        normalized_content_type = content_type.lower().split(";")[0].strip()
        normalized_filename = filename.lower()

        return (
            normalized_content_type in self.SUPPORTED_CONTENT_TYPES
            or normalized_filename.endswith(tuple(self.SUPPORTED_EXTENSIONS))
        )

    def parse(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str,
    ) -> ParsedDocument:
        try:
            document = pymupdf.open(
                stream=content,
                filetype="pdf",
            )
        except Exception as exc:
            raise DocumentParseError(
                f"Unable to open PDF document: {filename}"
            ) from exc

        try:
            pages: list[ParsedPage] = []
            ocr_page_count = 0

            for page_number, page in enumerate(document):
                text = page.get_text("text")
                source = "pdf"

                if not text.strip():
                    text = _ocr_page(page)
                    source = "pdf_ocr"

                    if text.strip():
                        ocr_page_count += 1

                pages.append(
                    ParsedPage(
                        index=page_number,
                        text=text,
                        metadata={
                            "source_type": source,
                            "page_number": page_number + 1,
                        },
                    )
                )

            full_text = "\n".join(
                page.text
                for page in pages
            )

            return ParsedDocument(
                text=full_text,
                filename=filename,
                content_type=content_type,
                pages=tuple(pages),
                metadata={
                    "parser": "pdf",
                    "page_count": len(pages),
                    "ocr_page_count": ocr_page_count,
                },
            )

        except Exception as exc:
            raise DocumentParseError(
                f"Unable to parse PDF document: {filename}"
            ) from exc

        finally:
            document.close()