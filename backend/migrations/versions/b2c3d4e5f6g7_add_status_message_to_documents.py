"""add_status_message_to_documents

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add status_message column to documents table."""
    op.add_column('documents', sa.Column('status_message', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove status_message column from documents table."""
    op.drop_column('documents', 'status_message')
