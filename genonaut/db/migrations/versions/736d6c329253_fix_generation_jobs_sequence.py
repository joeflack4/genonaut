"""fix generation_jobs sequence

Revision ID: 736d6c329253
Revises: d29303e76c9e
Create Date: 2025-10-24 23:04:57.499537

Notes:
- The generation_jobs table was not included in the bd75737333d5 migration
  that converted SERIAL sequences to IDENTITY columns
- This caused the sequence to be out of sync with the data
- This migration ensures the sequence is properly reset to the next available ID

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '736d6c329253'
down_revision: Union[str, Sequence[str], None] = 'd29303e76c9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Reset the generation_jobs sequence to the next available ID
    # This fixes the issue where the sequence was out of sync after the
    # SERIAL to IDENTITY conversion in migration bd75737333d5
    op.execute(
        "SELECT setval(pg_get_serial_sequence('generation_jobs', 'id'), "
        "COALESCE((SELECT MAX(id) FROM generation_jobs), 0) + 1, false);"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # No downgrade needed - this migration only resets a sequence value
    # which is idempotent and safe
    pass
