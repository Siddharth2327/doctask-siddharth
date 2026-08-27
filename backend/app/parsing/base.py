from abc import ABC, abstractmethod

from app.parsing.models import ParsedDocument


class DocumentParser(ABC):
    """Abstract interface for document parsers."""

    @abstractmethod
    def supports(self, content_type: str, filename: str) -> bool:
        """Return whether this parser can handle the document."""
        raise NotImplementedError

    @abstractmethod
    def parse(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str,
    ) -> ParsedDocument:
        """Parse document bytes into normalized document content."""
        raise NotImplementedError