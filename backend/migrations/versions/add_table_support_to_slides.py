"""add table support to slides

Revision ID: add_table_support
Revises: add_hierarchical_fields
Create Date: 2025-11-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = 'add_table_support'
down_revision = 'add_hierarchical_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add table support columns to slides table
    op.add_column('slides', sa.Column('table_data', JSON, nullable=True))
    op.add_column('slides', sa.Column('has_table', sa.Boolean(), server_default='false', nullable=False))


def downgrade():
    # Remove table support columns from slides table
    op.drop_column('slides', 'has_table')
    op.drop_column('slides', 'table_data')
