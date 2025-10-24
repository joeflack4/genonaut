"""remove foreign key constraint from generation_events

Revision ID: d29303e76c9e
Revises: d1ed18f7e5f3
Create Date: 2025-10-24 01:41:07.780098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd29303e76c9e'
down_revision: Union[str, Sequence[str], None] = 'd1ed18f7e5f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove foreign key constraint from generation_events.user_id.

    For analytics data, we want to retain events even if users are deleted.
    The foreign key constraint prevents this and isn't necessary for analytics.
    """
    # Drop foreign key constraint on generation_events.user_id
    op.drop_constraint('generation_events_user_id_fkey', 'generation_events', type_='foreignkey')


def downgrade() -> None:
    """Restore foreign key constraint."""
    # Restore foreign key constraint
    op.create_foreign_key(
        'generation_events_user_id_fkey',
        'generation_events',
        'users',
        ['user_id'],
        ['id']
    )
