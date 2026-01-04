"""add_document_summaries_table

Revision ID: a1b2c3d4e5f6
Revises: d6a64881428a
Create Date: 2026-01-03 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd6a64881428a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create document_summaries table for storing visual summary data."""
    op.create_table(
        'document_summaries',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id'), nullable=False, unique=True),
        sa.Column('executive_summary', sa.Text(), nullable=True),
        sa.Column('stats', sa.JSON(), nullable=True),
        sa.Column('key_concepts', sa.JSON(), nullable=True),
        sa.Column('topic_distribution', sa.JSON(), nullable=True),
        sa.Column('main_takeaways', sa.JSON(), nullable=True),
        sa.Column('learning_objectives', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_document_summaries_id'), 'document_summaries', ['id'], unique=False)


def downgrade() -> None:
    """Drop document_summaries table."""
    op.drop_index(op.f('ix_document_summaries_id'), table_name='document_summaries')
    op.drop_table('document_summaries')
