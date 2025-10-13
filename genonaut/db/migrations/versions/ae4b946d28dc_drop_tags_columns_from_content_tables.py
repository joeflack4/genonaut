"""Drop tags columns from content tables

Revision ID: ae4b946d28dc
Revises: 5498bb4ad836
Create Date: 2025-10-13 14:26:11.953963

NOTE: This migration removes the redundant tags UUID[] columns now that
we have the content_tags junction table providing optimized tag queries.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'ae4b946d28dc'
down_revision: Union[str, Sequence[str], None] = '5498bb4ad836'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop tags columns - now using content_tags junction table exclusively."""
    # Drop tags column from content_items
    op.drop_column('content_items', 'tags')

    # Drop tags column from content_items_auto
    op.drop_column('content_items_auto', 'tags')


def downgrade() -> None:
    """Restore tags columns if needed (though they won't be populated)."""
    # Import UUIDArrayColumn for proper column recreation
    from genonaut.db.schema import UUIDArrayColumn

    # Recreate tags column in content_items
    op.add_column('content_items',
        sa.Column('tags', UUIDArrayColumn(), nullable=True)
    )

    # Recreate tags column in content_items_auto
    op.add_column('content_items_auto',
        sa.Column('tags', UUIDArrayColumn(), nullable=True)
    )
