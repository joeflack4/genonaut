"""Create content_tags junction table

Revision ID: 5498bb4ad836
Revises: 4b0146ebf04b
Create Date: 2025-10-13 04:29:15.574606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '5498bb4ad836'
down_revision: Union[str, Sequence[str], None] = '4b0146ebf04b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create content_tags junction table for normalized tag relationships.

    This table replaces the tags UUID[] arrays in content_items and content_items_auto
    with a proper many-to-many relationship through a junction table.

    Schema:
    - content_id: INTEGER (references either content_items.id or content_items_auto.id)
    - content_source: VARCHAR(10) ('regular' or 'auto') - distinguishes which table
    - tag_id: UUID (foreign key to tags.id)
    - Primary key: (content_id, content_source, tag_id)

    Indexes:
    - idx_content_tags_tag_content: (tag_id, content_id) - for "all content with this tag"
    - idx_content_tags_content: (content_id, content_source) - for "all tags for this content"
    """
    # Create content_tags junction table
    op.create_table(
        'content_tags',
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('content_source', sa.String(length=10), nullable=False),
        sa.Column('tag_id', UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('content_id', 'content_source', 'tag_id'),
        comment='Junction table for many-to-many relationship between content and tags'
    )

    # Index for querying "all content with this tag" (tag -> content lookup)
    # This is the primary query pattern for gallery filtering
    op.create_index(
        'idx_content_tags_tag_content',
        'content_tags',
        ['tag_id', 'content_id'],
        unique=False
    )

    # Index for querying "all tags for this content" (content -> tags lookup)
    op.create_index(
        'idx_content_tags_content',
        'content_tags',
        ['content_id', 'content_source'],
        unique=False
    )


def downgrade() -> None:
    """Drop content_tags junction table and its indexes."""
    op.drop_index('idx_content_tags_content', table_name='content_tags')
    op.drop_index('idx_content_tags_tag_content', table_name='content_tags')
    op.drop_table('content_tags')
