from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CommitEvent(Base):
    """Audit record of a commit decision for one finding.

    The unique constraint on `finding_id` is what makes commit
    idempotent (T073): a repeated commit request for a finding that
    already has a CommitEvent is a no-op rather than a duplicate write.
    """

    __tablename__ = "commit_events"

    __table_args__ = (
        UniqueConstraint(
            "finding_id",
            name="uq_commit_event_finding",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    finding_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
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

    field: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # committed | skipped_rejected
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    committed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
