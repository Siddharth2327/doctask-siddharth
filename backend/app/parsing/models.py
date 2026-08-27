from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ParsedPage:
    """Normalized content extracted from a single source page/section."""

    index: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedDocument:
    """Normalized representation of a parsed document."""

    text: str
    filename: str
    content_type: str
    pages: tuple[ParsedPage, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)