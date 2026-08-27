"""add token usage tracking to runs

Revision ID: d5b7c3a9f1e4
Revises: c4a8f0e1d6b2
Create Date: 2026-08-21 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5b7c3a9f1e4'
down_revision: Union[str, Sequence[str], None] = 'c4a8f0e1d6b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'runs',
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'runs',
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'runs',
        sa.Column('estimated_cost', sa.Float(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('runs', 'estimated_cost')
    op.drop_column('runs', 'output_tokens')
    op.drop_column('runs', 'input_tokens')
