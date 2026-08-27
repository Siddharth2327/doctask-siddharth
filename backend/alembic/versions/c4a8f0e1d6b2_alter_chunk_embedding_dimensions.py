"""alter chunk embedding dimensions to match settings

Revision ID: c4a8f0e1d6b2
Revises: 9f3d1a7c2e88
Create Date: 2026-08-21 00:00:00.000000

This migration is intentionally dynamic: it reads
`settings.embedding_dimensions` at upgrade time and alters the
`chunks.embedding` column to that size. It is a no-op if the column is
already that size (the common case: nobody has changed
EMBEDDING_DIMENSIONS from its default of 32).

IMPORTANT: pgvector requires every row in a vector column to have the
same dimension. If you change EMBEDDING_DIMENSIONS (e.g. to switch to
a real embedding provider like OpenAI at 1536 dimensions) on a
database that already has chunks, you must either:

  1. Truncate the chunks table first (existing chunks will be
     re-created from their source documents next run), or
  2. Re-embed existing chunks at the new dimension BEFORE running this
     migration (see scripts/reembed_chunks.py), then run it.

Running this migration against non-empty chunks with mismatched
dimensions will fail loudly (a Postgres error), not silently corrupt
data.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from app.core.config import settings

# revision identifiers, used by Alembic.
revision: str = 'c4a8f0e1d6b2'
down_revision: Union[str, Sequence[str], None] = '9f3d1a7c2e88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _current_dimensions() -> int | None:
    connection = op.get_bind()

    result = connection.execute(
        sa.text(
            "SELECT atttypmod FROM pg_attribute "
            "WHERE attrelid = 'chunks'::regclass AND attname = 'embedding'"
        )
    ).scalar()

    # pgvector stores dimension as atttypmod directly (not offset by 4
    # like varchar); a value <= 0 means "unconstrained".
    return result if result and result > 0 else None


def upgrade() -> None:
    target_dimensions = settings.embedding_dimensions
    current = _current_dimensions()

    if current == target_dimensions:
        return

    op.alter_column(
        'chunks',
        'embedding',
        type_=Vector(target_dimensions),
        postgresql_using='embedding',
    )


def downgrade() -> None:
    # Dimension changes are not reversible without knowing the prior
    # value; this is a deliberate no-op. Restore from a backup taken
    # before upgrading if you need to revert.
    pass
