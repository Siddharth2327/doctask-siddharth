from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Evidence(Base):
    """A traceable piece of source evidence backing an extracted fact.

    Every meaningful claim produced by the agent must be able to point
    back to the exact document, document version, and location it came
    from. Evidence rows are the durable, queryable counterpart to the
    in-memory `EvidenceReference` objects attached to extracted facts
    during a workflow run (see app.agents.extraction).
    """

    __tablename__ = "evidence"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    run_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
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

    # The extracted-fact field this evidence supports, e.g. "contract_value".
    # Nullable because evidence may later be produced outside fact
    # extraction (e.g. rule findings referencing a raw source passage).
    field: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Human-readable source location, e.g. "page 2" or "section 3.1".
    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Deterministic chunk identifier. Populated once chunking (T051) is
    # implemented; kept nullable now so evidence can be recorded before
    # chunking exists without a schema change.
    chunk_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # The supporting source text itself.
    quote: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    document = relationship("Document")
    document_version = relationship("DocumentVersion")
