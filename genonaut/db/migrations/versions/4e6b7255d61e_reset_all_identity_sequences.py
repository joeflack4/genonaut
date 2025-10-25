"""reset all identity sequences

Revision ID: 4e6b7255d61e
Revises: 736d6c329253
Create Date: 2025-10-24 23:26:37.312106

Notes:
- This migration resets ALL IDENTITY sequences to be in sync with their table data
- This is necessary because migration bd75737333d5 converted SERIAL to IDENTITY
  but did not include all tables in its reset logic, and some sequences got
  out of sync after data seeding
- This migration is idempotent and safe to run multiple times
- Fixes the issue where sequences were trying to use already-taken IDs,
  causing UniqueViolation errors

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e6b7255d61e'
down_revision: Union[str, Sequence[str], None] = '736d6c329253'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All tables with IDENTITY primary keys that need sequence resets
TABLES_WITH_IDENTITY_PKS = [
    'available_models',
    'content_items',
    'content_items_auto',
    'flagged_content',
    'generation_jobs',
    'recommendations',
    'tag_ratings',
    'user_interactions',
    'user_notifications',
    'user_search_history',
]


def upgrade() -> None:
    """Upgrade schema."""
    # Reset all IDENTITY sequences to the next available ID
    # This ensures sequences are in sync with actual data in the tables
    for table_name in TABLES_WITH_IDENTITY_PKS:
        op.execute(
            f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, false);"
        )


def downgrade() -> None:
    """Downgrade schema."""
    # No downgrade needed - resetting sequences is idempotent and safe
    # The sequences will remain at their correct values
    pass
