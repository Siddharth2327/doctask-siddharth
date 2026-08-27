from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy import Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Run(Base):
    """A single agentic analysis run.

    `id` is used as the LangGraph checkpointer `thread_id`, so the
    durable workflow state (see app.agents.checkpoint) and this row's
    domain-level status always refer to the same run. Status here is a
    coarse summary for API/reporting purposes; the authoritative
    per-node execution history lives in the LangGraph checkpoint.
    """

    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    case_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    document_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    document_version_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # pending | running | pending_review | completed | failed
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    input_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    output_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    estimated_cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
