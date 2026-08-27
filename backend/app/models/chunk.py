from datetime import datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base

# Driven by settings.embedding_dimensions so the column always matches
# whichever embedding provider is configured (mock/deterministic
# default to 32; a real provider like OpenAI is typically configured
# to 512-1536). Changing this value after chunks already exist
# requires a migration (see alembic/versions -- "alter chunk embedding
# dimensions") AND re-embedding existing chunks (see
# scripts/reembed_chunks.py) -- a vector column has one fixed size.
EMBEDDING_DIMENSIONS = settings.embedding_dimensions


class Chunk(Base):
    """A retrievable, page-aware segment of a parsed document version.

    Chunks are the unit that gets embedded and searched via pgvector
    (T053). Evidence rows (see app.models.evidence) reference a chunk's
    id via `Evidence.chunk_id` once a piece of extracted evidence has
    been grounded against a specific chunk.
    """

    __tablename__ = "chunks"

    __table_args__ = (
        UniqueConstraint(
            "document_version_id",
            "chunk_index",
            name="uq_chunk_version_index",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    document_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    document_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    page_index: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Deterministic content-addressed identifier, stable across re-runs
    # of the same document version (T051: "deterministic chunk IDs").
    chunk_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    document = relationship("Document")
    document_version = relationship("DocumentVersion")
