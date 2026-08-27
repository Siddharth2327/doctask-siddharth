from app.parsing.base import DocumentParser
from app.parsing.errors import UnsupportedDocumentError
from app.parsing.pdf import PdfParser
from app.parsing.text import TextParser
from app.parsing.docx import DocxParser
from app.parsing.image_ocr import ImageOcrParser

PARSERS: tuple[DocumentParser, ...] = (
    TextParser(),
    PdfParser(),
    DocxParser(),
    ImageOcrParser(),
)


def get_parser(
    *,
    content_type: str,
    filename: str,
) -> DocumentParser:
    """Return the first parser capable of handling the document."""

    for parser in PARSERS:
        if parser.supports(content_type, filename):
            return parser

    raise UnsupportedDocumentError(
        f"Unsupported document format: {filename} ({content_type})"
    )
