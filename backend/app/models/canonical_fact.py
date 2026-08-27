from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CanonicalFact(Base):
    """The current committed value for one field of one case.

    A "case" groups the documents that describe a single real-world
    subject (for the Task 1 domain: one vendor contract and its
    amendments/invoices/renewal notices). Only CommitService writes to
    this table, and only from APPROVED findings (T073) -- it is the
    system's single source of truth for "what do we currently believe",
    always traceable back to the evidence that supports it.
    """

    __tablename__ = "canonical_facts"

    __table_args__ = (
        UniqueConstraint(
            "case_id",
            "field",
            name="uq_canonical_fact_case_field",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    case_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    field: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    evidence_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )

    document_version_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    run_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    finding_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="SET NULL"),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    evidence = relationship("Evidence")
    document_version = relationship("DocumentVersion")
