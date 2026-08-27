class DocumentParsingError(Exception):
    """Base exception for document parsing failures."""


class UnsupportedDocumentError(DocumentParsingError):
    """Raised when no parser supports the document format."""


class DocumentParseError(DocumentParsingError):
    """Raised when a supported document cannot be parsed."""