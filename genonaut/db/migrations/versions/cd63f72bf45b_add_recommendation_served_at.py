"""add_recommendation_served_at

Revision ID: cd63f72bf45b
Revises: 754d69929ccd
Create Date: 2025-09-19 20:50:36.031810

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd63f72bf45b'
down_revision: Union[str, Sequence[str], None] = '754d69929ccd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('recommendations', sa.Column('served_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('recommendations', 'served_at')
