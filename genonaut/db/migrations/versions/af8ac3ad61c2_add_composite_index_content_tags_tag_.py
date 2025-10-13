"""add_composite_index_content_tags_tag_source_content

Revision ID: af8ac3ad61c2
Revises: ae4b946d28dc
Create Date: 2025-10-13 22:26:28.832425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af8ac3ad61c2'
down_revision: Union[str, Sequence[str], None] = 'ae4b946d28dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite index on content_tags(tag_id, content_source, content_id)."""
    op.create_index(
        'idx_content_tags_tag_source_content',
        'content_tags',
        ['tag_id', 'content_source', 'content_id'],
        unique=False
    )


def downgrade() -> None:
    """Remove composite index."""
    op.drop_index('idx_content_tags_tag_source_content', table_name='content_tags')
