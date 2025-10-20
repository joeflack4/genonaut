"""remove redundant indexes on content tables

Revision ID: 0a277157bd85
Revises: 35129ad8b067
Create Date: 2025-10-20 19:30:00.000000

This migration removes redundant indexes identified in Phase 4.3: Index Cleanup.

Indexes removed:
1. idx_content_items_created_at_desc - redundant with idx_content_items_created_id_desc
2. idx_content_items_auto_created_at_desc - redundant with idx_content_items_auto_created_id_desc
3. idx_content_items_type_created - redundant with ix_content_items_content_type (heavily used)
4. idx_content_items_auto_type_created - redundant with ix_content_items_auto_content_type (heavily used)

Space savings: ~60 MB
See: notes/perf-updates-2025-10-17.md - Proposal 4, Phase 4.3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a277157bd85'
down_revision: Union[str, Sequence[str], None] = '35129ad8b067'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove redundant indexes on content_items and content_items_auto tables."""

    # Drop redundant created_at indexes (covered by composite created_at, id DESC indexes)
    op.drop_index('idx_content_items_created_at_desc', table_name='content_items')
    op.drop_index('idx_content_items_auto_created_at_desc', table_name='content_items_auto')

    # Drop redundant type+created indexes (simple content_type index is heavily used)
    op.drop_index('idx_content_items_type_created', table_name='content_items')
    op.drop_index('idx_content_items_auto_type_created', table_name='content_items_auto')


def downgrade() -> None:
    """Restore removed indexes if needed."""

    # Recreate type+created indexes
    op.create_index(
        'idx_content_items_type_created',
        'content_items',
        ['content_type', sa.text('created_at DESC')],
        unique=False
    )
    op.create_index(
        'idx_content_items_auto_type_created',
        'content_items_auto',
        ['content_type', sa.text('created_at DESC')],
        unique=False
    )

    # Recreate created_at DESC indexes
    op.create_index(
        'idx_content_items_created_at_desc',
        'content_items',
        [sa.text('created_at DESC')],
        unique=False
    )
    op.create_index(
        'idx_content_items_auto_created_at_desc',
        'content_items_auto',
        [sa.text('created_at DESC')],
        unique=False
    )
