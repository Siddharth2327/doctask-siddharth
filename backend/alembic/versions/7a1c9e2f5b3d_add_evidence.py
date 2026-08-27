"""add evidence

Revision ID: 7a1c9e2f5b3d
Revises: 42b10f331d4b
Create Date: 2026-08-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1c9e2f5b3d'
down_revision: Union[str, Sequence[str], None] = '42b10f331d4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'evidence',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('run_id', sa.String(length=255), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('document_version_id', sa.UUID(), nullable=False),
        sa.Column('field', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('chunk_id', sa.String(length=255), nullable=True),
        sa.Column('quote', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['document_id'], ['documents.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['document_version_id'], ['document_versions.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_evidence_document_id'),
        'evidence',
        ['document_id'],
    )
    op.create_index(
        op.f('ix_evidence_document_version_id'),
        'evidence',
        ['document_version_id'],
    )
    op.create_index(
        op.f('ix_evidence_run_id'),
        'evidence',
        ['run_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_evidence_run_id'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_document_version_id'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_document_id'), table_name='evidence')
    op.drop_table('evidence')
