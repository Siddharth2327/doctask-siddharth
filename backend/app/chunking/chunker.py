from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.parsing.models import ParsedDocument

# Kept intentionally simple (T051 / "do not over-engineer retrieval"):
# split each page's text into paragraph-sized chunks with a soft
# character budget. No sentence-embedding-aware splitting, no overlap
# window tuning -- just enough structure to make retrieval useful and
# evidence locations meaningful.
DEFAULT_MAX_CHUNK_CHARS = 800


@dataclass(frozen=True)
class Chunk:
    """A single chunk produced from a parsed document, prior to persistence."""

    index: int
    page_index: int | None
    text: str
    chunk_hash: str


def _chunk_id(
    *,
    document_version_id: str,
    index: int,
    text: str,
) -> str:
    """Deterministic content-addressed chunk id.

    Stable across re-runs of the same document version: the same page
    content at the same position always produces the same hash, so
    re-chunking an unchanged version is idempotent.
    """

    digest_input = f"{document_version_id}:{index}:{text}".encode("utf-8")

    return hashlib.sha256(digest_input).hexdigest()


def _split_paragraphs(text: str) -> list[str]:
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]

    return paragraphs or ([text.strip()] if text.strip() else [])


def _pack_paragraphs(
    paragraphs: list[str],
    *,
    max_chars: int,
) -> list[str]:
    """Greedily pack paragraphs into chunks under the character budget.

    A single paragraph longer than the budget becomes its own chunk
    rather than being silently dropped or truncated.
    """

    packed: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        added_len = len(paragraph) + (2 if current else 0)

        if current and current_len + added_len > max_chars:
            packed.append("\n\n".join(current))
            current = []
            current_len = 0

        current.append(paragraph)
        current_len += len(paragraph) + (2 if len(current) > 1 else 0)

    if current:
        packed.append("\n\n".join(current))

    return packed


def chunk_document(
    document: ParsedDocument,
    *,
    document_version_id: str,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
) -> list[Chunk]:
    """Split a parsed document into deterministic, page-aware chunks."""

    chunks: list[Chunk] = []
    index = 0

    # Fall back to a single synthetic page when the parser did not
    # provide page/section structure (e.g. plain text documents).
    sources = (
        [(page.index, page.text) for page in document.pages]
        if document.pages
        else [(None, document.text)]
    )

    for page_index, page_text in sources:
        for paragraph_chunk in _pack_paragraphs(
            _split_paragraphs(page_text),
            max_chars=max_chunk_chars,
        ):
            chunk_hash = _chunk_id(
                document_version_id=document_version_id,
                index=index,
                text=paragraph_chunk,
            )

            chunks.append(
                Chunk(
                    index=index,
                    page_index=page_index,
                    text=paragraph_chunk,
                    chunk_hash=chunk_hash,
                )
            )
            index += 1

    return chunks
