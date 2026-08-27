"""add retrieval and workflow domain tables

Revision ID: 9f3d1a7c2e88
Revises: 7a1c9e2f5b3d
Create Date: 2026-08-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '9f3d1a7c2e88'
down_revision: Union[str, Sequence[str], None] = '7a1c9e2f5b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSIONS = 32


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # --- chunks ---------------------------------------------------------
    op.create_table(
        'chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('document_version_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('page_index', sa.Integer(), nullable=True),
        sa.Column('chunk_hash', sa.String(length=64), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(EMBEDDING_DIMENSIONS), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_version_id', 'chunk_index', name='uq_chunk_version_index'),
    )
    op.create_index(op.f('ix_chunks_document_id'), 'chunks', ['document_id'])
    op.create_index(op.f('ix_chunks_document_version_id'), 'chunks', ['document_version_id'])

    # --- runs -------------------------------------------------------------
    op.create_table(
        'runs',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('case_id', sa.String(length=255), nullable=False),
        sa.Column('document_id', sa.String(length=255), nullable=False),
        sa.Column('document_version_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_runs_case_id'), 'runs', ['case_id'])

    # --- conflicts ----------------------------------------------------
    op.create_table(
        'conflicts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('run_id', sa.String(length=255), nullable=False),
        sa.Column('case_id', sa.String(length=255), nullable=False),
        sa.Column('field', sa.String(length=255), nullable=False),
        sa.Column('existing_value', sa.Text(), nullable=True),
        sa.Column('existing_evidence_id', sa.UUID(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=False),
        sa.Column('new_evidence_id', sa.UUID(), nullable=True),
        sa.Column('document_version_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['existing_evidence_id'], ['evidence.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['new_evidence_id'], ['evidence.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_conflicts_run_id'), 'conflicts', ['run_id'])
    op.create_index(op.f('ix_conflicts_case_id'), 'conflicts', ['case_id'])

    # --- findings -------------------------------------------------------
    op.create_table(
        'findings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('run_id', sa.String(length=255), nullable=False),
        sa.Column('case_id', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('field', sa.String(length=255), nullable=True),
        sa.Column('proposed_value', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('evidence_ids', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('conflict_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('reviewer', sa.String(length=255), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conflict_id'], ['conflicts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_findings_run_id'), 'findings', ['run_id'])
    op.create_index(op.f('ix_findings_case_id'), 'findings', ['case_id'])
    op.create_index(op.f('ix_findings_status'), 'findings', ['status'])

    # --- canonical_facts ------------------------------------------------
    op.create_table(
        'canonical_facts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('case_id', sa.String(length=255), nullable=False),
        sa.Column('field', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('evidence_id', sa.UUID(), nullable=True),
        sa.Column('document_version_id', sa.UUID(), nullable=True),
        sa.Column('run_id', sa.String(length=255), nullable=False),
        sa.Column('finding_id', sa.UUID(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_id', 'field', name='uq_canonical_fact_case_field'),
    )
    op.create_index(op.f('ix_canonical_facts_case_id'), 'canonical_facts', ['case_id'])

    # --- commit_events ----------------------------------------------------
    op.create_table(
        'commit_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('finding_id', sa.UUID(), nullable=False),
        sa.Column('run_id', sa.String(length=255), nullable=False),
        sa.Column('case_id', sa.String(length=255), nullable=False),
        sa.Column('field', sa.String(length=255), nullable=True),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('committed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('finding_id', name='uq_commit_event_finding'),
    )
    op.create_index(op.f('ix_commit_events_run_id'), 'commit_events', ['run_id'])
    op.create_index(op.f('ix_commit_events_case_id'), 'commit_events', ['case_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('commit_events')
    op.drop_table('canonical_facts')
    op.drop_table('findings')
    op.drop_table('conflicts')
    op.drop_table('runs')
    op.drop_table('chunks')
