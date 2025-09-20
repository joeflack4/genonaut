"""add_updated_timestamps

Revision ID: 754d69929ccd
Revises: 965558fecc0b
Create Date: 2025-09-19 20:49:12.766703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '754d69929ccd'
down_revision: Union[str, Sequence[str], None] = '965558fecc0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'content_items',
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
    )
    op.add_column(
        'generation_jobs',
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
    )

    # Drop server defaults after backfilling existing rows
    op.alter_column('content_items', 'updated_at', server_default=None)
    op.alter_column('generation_jobs', 'updated_at', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('generation_jobs', 'updated_at')
    op.drop_column('content_items', 'updated_at')
