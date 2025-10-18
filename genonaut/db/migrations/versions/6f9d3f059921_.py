"""Create partitioned parent table content_items_all

Revision ID: 6f9d3f059921
Revises: e804355b2a87
Create Date: 2025-10-18 02:57:55.954306

This migration implements Phase 11: Partitioned Parent Table for performance optimization.

Changes:
1. Add path_thumbs_alt_res column to both content tables (missing from current schema)
2. Add source_type GENERATED column to both tables for partition key
3. Create content_items_all parent table (partitioned by source_type)
4. Attach existing tables as partitions
5. Create partition-specific indexes for keyset pagination

See: notes/perf-report-2025-10-17.md - Proposal 11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from genonaut.db.schema import JSONColumn


# revision identifiers, used by Alembic.
revision: str = '6f9d3f059921'
down_revision: Union[str, Sequence[str], None] = 'e804355b2a87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to use partitioned parent table."""

    # Phase 11.2: Schema Alignment
    # Note: path_thumbs_alt_res already exists in both tables (added manually)

    # CRITICAL: Column order must match exactly for partitioning to work
    # content_items has: ..., created_at, tags, quality_score, is_public, is_private, updated_at, ...
    # content_items_auto has: ..., created_at, updated_at, tags, quality_score, is_public, is_private, ...
    # We need to reorder content_items_auto to match content_items

    # Recreate content_items_auto with correct column order
    # This is safe because we're in a transaction - if anything fails, it all rolls back
    op.execute("""
        -- Create temp table with correct column order (no FK constraint initially)
        CREATE TABLE content_items_auto_new (
            id                  integer       PRIMARY KEY,
            title               varchar(255)  NOT NULL,
            content_type        varchar(50)   NOT NULL,
            content_data        text          NOT NULL,
            item_metadata       jsonb,
            creator_id          integer       NOT NULL,
            created_at          timestamp without time zone NOT NULL,
            tags                jsonb,
            quality_score       double precision,
            is_public           boolean       NOT NULL,
            is_private          boolean       NOT NULL,
            updated_at          timestamp without time zone NOT NULL,
            path_thumb          varchar(512),
            prompt              varchar(20000) NOT NULL,
            path_thumbs_alt_res jsonb
        )
    """)

    # Copy data with explicit column mapping (use COALESCE for potentially null columns)
    op.execute("""
        INSERT INTO content_items_auto_new (
            id, title, content_type, content_data, item_metadata, creator_id,
            created_at, tags, quality_score, is_public, is_private, updated_at,
            path_thumb, prompt, path_thumbs_alt_res
        )
        SELECT
            content_items_auto.id,
            content_items_auto.title,
            content_items_auto.content_type,
            content_items_auto.content_data,
            content_items_auto.item_metadata,
            content_items_auto.creator_id,
            content_items_auto.created_at,
            content_items_auto.tags,
            content_items_auto.quality_score,
            content_items_auto.is_public,
            content_items_auto.is_private,
            content_items_auto.updated_at,
            content_items_auto.path_thumb,
            content_items_auto.prompt,
            content_items_auto.path_thumbs_alt_res
        FROM content_items_auto
    """)

    # Drop old table and rename new one
    op.execute("DROP TABLE content_items_auto CASCADE")
    op.execute("ALTER TABLE content_items_auto_new RENAME TO content_items_auto")

    # Recreate FK constraint (same as original)
    op.create_foreign_key(
        'content_items_auto_creator_id_fkey',
        'content_items_auto', 'users',
        ['creator_id'], ['id']
    )

    # Recreate indexes that were dropped with CASCADE
    op.create_index('cia_title_fts_idx', 'content_items_auto',
                    [sa.text("to_tsvector('english'::regconfig, COALESCE(title, ''::character varying)::text)")],
                    unique=False, postgresql_using='gin')
    op.create_index('idx_content_items_auto_created_at_desc', 'content_items_auto',
                    [sa.text('created_at DESC')], unique=False)
    op.create_index('idx_content_items_auto_creator_created', 'content_items_auto',
                    ['creator_id', sa.text('created_at DESC')], unique=False)
    op.create_index('idx_content_items_auto_quality_created', 'content_items_auto',
                    [sa.text('quality_score DESC'), sa.text('created_at DESC')], unique=False)
    op.create_index('idx_content_items_auto_type_created', 'content_items_auto',
                    ['content_type', sa.text('created_at DESC')], unique=False)
    op.create_index('idx_content_items_auto_public_created', 'content_items_auto',
                    [sa.text('created_at DESC')],
                    unique=False,
                    postgresql_where=sa.text('is_private = false'))
    op.create_index('idx_content_items_auto_metadata_gin', 'content_items_auto',
                    ['item_metadata'], unique=False, postgresql_using='gin')
    op.create_index('idx_content_items_auto_tags_gin', 'content_items_auto',
                    ['tags'], unique=False, postgresql_using='gin')
    op.create_index('ix_content_items_auto_content_type', 'content_items_auto',
                    ['content_type'], unique=False)
    op.create_index('ix_content_items_auto_creator_id', 'content_items_auto',
                    ['creator_id'], unique=False)

    # Add source_type GENERATED columns for partition key
    op.execute("""
        ALTER TABLE content_items
        ADD COLUMN source_type text
        GENERATED ALWAYS AS ('items') STORED
    """)

    op.execute("""
        ALTER TABLE content_items_auto
        ADD COLUMN source_type text
        GENERATED ALWAYS AS ('auto') STORED
    """)

    # Phase 11.3: Create Parent Table
    # Parent must have EXACT same columns in EXACT same order as children
    # Note: Cannot have FK constraints on partitioned tables - FKs remain on child tables
    op.execute("""
        CREATE TABLE content_items_all (
            id                  integer       NOT NULL,
            title               varchar(255)  NOT NULL,
            content_type        varchar(50)   NOT NULL,
            content_data        text          NOT NULL,
            item_metadata       jsonb,
            creator_id          integer       NOT NULL,
            created_at          timestamp without time zone NOT NULL,
            tags                jsonb,
            quality_score       double precision,
            is_public           boolean       NOT NULL,
            is_private          boolean       NOT NULL,
            updated_at          timestamp without time zone NOT NULL,
            path_thumb          varchar(512),
            prompt              varchar(20000) NOT NULL,
            path_thumbs_alt_res jsonb,
            source_type         text          NOT NULL,

            CONSTRAINT content_items_all_pkey PRIMARY KEY (id, source_type)
        ) PARTITION BY LIST (source_type)
    """)

    # Phase 11.4: Attach Partitions
    # Attach existing tables as partitions (no data movement - instant operation)
    op.execute("""
        ALTER TABLE content_items_all
        ATTACH PARTITION content_items
        FOR VALUES IN ('items')
    """)

    op.execute("""
        ALTER TABLE content_items_all
        ATTACH PARTITION content_items_auto
        FOR VALUES IN ('auto')
    """)

    # Phase 11.5: Create Indexes
    # Create partition-specific indexes for keyset pagination (created_at DESC, id DESC)
    # These support efficient cursor-based pagination implemented in Phase 6
    op.create_index(
        'idx_content_items_created_id_desc',
        'content_items',
        [sa.text('created_at DESC'), sa.text('id DESC')],
        unique=False
    )

    op.create_index(
        'idx_content_items_auto_created_id_desc',
        'content_items_auto',
        [sa.text('created_at DESC'), sa.text('id DESC')],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema - detach partitions and drop parent table."""

    # Drop partition indexes
    op.drop_index('idx_content_items_auto_created_id_desc', table_name='content_items_auto')
    op.drop_index('idx_content_items_created_id_desc', table_name='content_items')

    # Detach partitions (makes them standalone tables again)
    op.execute("ALTER TABLE content_items_all DETACH PARTITION content_items_auto")
    op.execute("ALTER TABLE content_items_all DETACH PARTITION content_items")

    # Drop parent table
    op.execute("DROP TABLE content_items_all")

    # Remove source_type columns
    op.drop_column('content_items_auto', 'source_type')
    op.drop_column('content_items', 'source_type')

    # Note: Not removing path_thumbs_alt_res in downgrade since it's used by the application
