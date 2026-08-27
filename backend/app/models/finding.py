from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Finding(Base):
    """An individually reviewable item produced from conflict detection
    or rule validation (T063).

    Findings are the unit of human review (T070/T071): each one is
    approved, rejected, or edited independently, and only approved
    findings are ever committed (T073).
    """

    __tablename__ = "findings"

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

    # conflict | rule_violation
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    field: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # The value that would be committed if this finding is approved.
    # Null for findings that only flag a problem (e.g. missing evidence)
    # without proposing a replacement value.
    proposed_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # low | medium | high
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="medium",
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # JSON-encoded list of Evidence ids supporting this finding.
    evidence_ids: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    conflict_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("conflicts.id", ondelete="SET NULL"),
        nullable=True,
    )

    # pending | approved | rejected | committed
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    reviewer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    review_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    conflict = relationship("Conflict")
