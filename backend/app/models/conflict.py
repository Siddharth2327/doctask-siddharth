from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Conflict(Base):
    """A detected contradiction between a newly extracted value and the
    currently committed CanonicalFact value for the same (case, field).

    Both sides are preserved -- the existing value is never silently
    overwritten (T060). Resolving a conflict happens only through the
    normal Finding -> human review -> commit path.
    """

    __tablename__ = "conflicts"

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

    case_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    field: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    existing_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    existing_evidence_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )

    new_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    new_evidence_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )

    document_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # open | resolved
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    existing_evidence = relationship(
        "Evidence",
        foreign_keys=[existing_evidence_id],
    )
    new_evidence = relationship(
        "Evidence",
        foreign_keys=[new_evidence_id],
    )
