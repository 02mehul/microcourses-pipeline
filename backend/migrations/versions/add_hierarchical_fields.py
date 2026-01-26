"""add hierarchical fields to slides and questions

Revision ID: add_hierarchical_fields
Revises: d6a64881428a
Create Date: 2025-11-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_hierarchical_fields'
down_revision = 'd6a64881428a'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to slides table
    op.add_column('slides', sa.Column('chapter_title', sa.String(), nullable=True))
    op.add_column('slides', sa.Column('subchapter_title', sa.String(), nullable=True))
    op.add_column('slides', sa.Column('subchapter_id', sa.String(), nullable=True))

    # Add new columns to questions table
    op.add_column('questions', sa.Column('subchapter_id', sa.String(), nullable=True))
    op.add_column('questions', sa.Column('subchapter_title', sa.String(), nullable=True))


def downgrade():
    # Remove columns from questions table
    op.drop_column('questions', 'subchapter_title')
    op.drop_column('questions', 'subchapter_id')

    # Remove columns from slides table
    op.drop_column('slides', 'subchapter_id')
    op.drop_column('slides', 'subchapter_title')
    op.drop_column('slides', 'chapter_title')
