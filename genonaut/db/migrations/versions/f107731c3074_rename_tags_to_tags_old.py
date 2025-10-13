"""Rename tags to tags_old

Revision ID: f107731c3074
Revises: a4903b37477c
Create Date: 2025-10-13 00:33:06.514667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f107731c3074'
down_revision: Union[str, Sequence[str], None] = 'a4903b37477c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename tags column to tags_old to preserve data
    # Drop indexes first, rename column, recreate indexes

    # content_items
    op.drop_index('idx_content_items_tags_gin', table_name='content_items', postgresql_using='gin')
    op.alter_column('content_items', 'tags', new_column_name='tags_old')
    op.create_index('idx_content_items_tags_gin', 'content_items', ['tags_old'], unique=False, postgresql_using='gin')

    # content_items_auto
    op.drop_index('idx_content_items_auto_tags_gin', table_name='content_items_auto', postgresql_using='gin')
    op.alter_column('content_items_auto', 'tags', new_column_name='tags_old')
    op.create_index('idx_content_items_auto_tags_gin', 'content_items_auto', ['tags_old'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename tags_old back to tags

    # content_items_auto
    op.drop_index('idx_content_items_auto_tags_gin', table_name='content_items_auto', postgresql_using='gin')
    op.alter_column('content_items_auto', 'tags_old', new_column_name='tags')
    op.create_index('idx_content_items_auto_tags_gin', 'content_items_auto', ['tags'], unique=False, postgresql_using='gin')

    # content_items
    op.drop_index('idx_content_items_tags_gin', table_name='content_items', postgresql_using='gin')
    op.alter_column('content_items', 'tags_old', new_column_name='tags')
    op.create_index('idx_content_items_tags_gin', 'content_items', ['tags'], unique=False, postgresql_using='gin')
