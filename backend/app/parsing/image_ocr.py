import io

import pytesseract
from PIL import Image

from app.parsing.base import DocumentParser
from app.parsing.errors import DocumentParseError
from app.parsing.models import ParsedDocument, ParsedPage


class ImageOcrParser(DocumentParser):
    """OCR parser for standalone scanned-image documents.

    Complements the OCR fallback inside PdfParser (which handles
    scanned *pages within a PDF*) by handling the case where the scan
    itself was uploaded directly as an image file, with no PDF
    wrapper. A single image is always treated as a single page.
    """

    SUPPORTED_CONTENT_TYPES = {
        "image/png",
        "image/jpeg",
        "image/tiff",
    }

    SUPPORTED_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
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
            image = Image.open(io.BytesIO(content))
            image.load()
        except Exception as exc:
            raise DocumentParseError(
                f"Unable to open image document: {filename}"
            ) from exc

        try:
            text = pytesseract.image_to_string(image)
        except pytesseract.TesseractNotFoundError as exc:
            raise DocumentParseError(
                "OCR engine (tesseract) is not installed on this host; "
                f"cannot parse image document: {filename}"
            ) from exc
        except Exception as exc:
            raise DocumentParseError(
                f"Unable to OCR image document: {filename}"
            ) from exc

        page = ParsedPage(
            index=0,
            text=text,
            metadata={
                "source_type": "image_ocr",
                "page_number": 1,
            },
        )

        return ParsedDocument(
            text=text,
            filename=filename,
            content_type=content_type,
            pages=(page,),
            metadata={
                "parser": "image_ocr",
                "page_count": 1,
            },
        )
