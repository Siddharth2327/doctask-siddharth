from app.parsing.base import DocumentParser
from app.parsing.errors import DocumentParseError
from app.parsing.models import ParsedDocument, ParsedPage


class TextParser(DocumentParser):
    """Parser for plain-text documents."""

    SUPPORTED_CONTENT_TYPES = {
        "text/plain",
    }

    SUPPORTED_EXTENSIONS = {
        ".txt",
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
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentParseError(
                f"Unable to decode text document: {filename}"
            ) from exc

        page = ParsedPage(
            index=0,
            text=text,
            metadata={
                "source_type": "text",
            },
        )

        return ParsedDocument(
            text=text,
            filename=filename,
            content_type=content_type,
            pages=(page,),
            metadata={
                "parser": "text",
            },
        )