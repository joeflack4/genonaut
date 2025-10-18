"""Create partitioned parent table content_items_all

Revision ID: 86456c44a065
Revises: e7526785bd0d
Create Date: 2025-10-18 04:25:11.707034

This migration implements Phase 11: Partitioned Parent Table for performance optimization.

Phases implemented:
- Phase 11.3: Create Parent Table (partitioned by source_type)
- Phase 11.4: Attach Partitions (attach existing content_items and content_items_auto)
- Phase 11.5: Create Indexes (keyset pagination indexes on each partition)

Prerequisites:
- Both content_items and content_items_auto have identical schemas (13 columns)
- source_type GENERATED column added to both tables (previous migration)

Benefits:
- Eliminates UNION ALL overhead - queries use single logical table
- PostgreSQL partition pruning when filtering by source_type
- MergeAppend optimization for ORDER BY operations
- Simpler cursor pagination (single table instead of multi-table encoding)

See: notes/perf-updates-2025-10-17.md - Proposal 11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86456c44a065'
down_revision: Union[str, Sequence[str], None] = 'e7526785bd0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to use partitioned parent table.

    Strategy: Create parent table and attach partitions WITHOUT dropping existing PKs/FKs.
    Uses per-child unique indexes that get attached to parent's composite PK.
    This preserves all existing foreign key relationships.
    """

    # Step 1: Ensure source_type is NOT NULL (should already be from previous migration)
    op.execute("ALTER TABLE content_items ALTER COLUMN source_type SET NOT NULL")
    op.execute("ALTER TABLE content_items_auto ALTER COLUMN source_type SET NOT NULL")

    # Step 2: Create per-child unique indexes (id, source_type)
    # These will be attached to the parent's partitioned unique index
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS items_uidx_id_src
        ON content_items (id, source_type)
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS auto_uidx_id_src
        ON content_items_auto (id, source_type)
    """)

    # Step 3: Create parent table WITHOUT PRIMARY KEY initially
    # Must have EXACT same columns in EXACT same order as child tables
    op.execute("""
        CREATE TABLE content_items_all (
            id                  integer       NOT NULL,
            title               varchar(255)  NOT NULL,
            content_type        varchar(50)   NOT NULL,
            content_data        text          NOT NULL,
            item_metadata       jsonb,
            creator_id          uuid          NOT NULL,
            created_at          timestamp without time zone NOT NULL,
            updated_at          timestamp without time zone NOT NULL,
            quality_score       double precision,
            is_private          boolean       NOT NULL DEFAULT false,
            path_thumb          varchar(512),
            prompt              varchar(20000) NOT NULL,
            path_thumbs_alt_res jsonb,
            source_type         text          NOT NULL
        ) PARTITION BY LIST (source_type)
    """)

    # Step 4: Attach partitions to parent
    op.execute("""
        ALTER TABLE content_items_all
        ATTACH PARTITION content_items FOR VALUES IN ('items')
    """)

    op.execute("""
        ALTER TABLE content_items_all
        ATTACH PARTITION content_items_auto FOR VALUES IN ('auto')
    """)

    # Step 5: Create partitioned unique index on parent
    op.execute("""
        CREATE UNIQUE INDEX content_items_all_uidx_id_src
        ON content_items_all (id, source_type)
    """)

    # Step 6: Attach child indexes to parent unique index
    op.execute("""
        ALTER INDEX content_items_all_uidx_id_src
        ATTACH PARTITION items_uidx_id_src
    """)

    op.execute("""
        ALTER INDEX content_items_all_uidx_id_src
        ATTACH PARTITION auto_uidx_id_src
    """)

    # Step 7: Note - cannot add PRIMARY KEY on partitioned table using USING INDEX
    # The partitioned unique index content_items_all_uidx_id_src serves the same purpose
    # PostgreSQL will use this index to enforce uniqueness across partitions

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
    """Downgrade schema - detach partitions and drop parent table.

    Reverses the partitioning setup while preserving original PKs and FKs.
    """

    # Drop keyset pagination indexes
    op.drop_index('idx_content_items_auto_created_id_desc', table_name='content_items_auto')
    op.drop_index('idx_content_items_created_id_desc', table_name='content_items')

    # Detach partitions (makes them standalone tables again)
    # This also detaches the child indexes from the parent index
    op.execute("ALTER TABLE content_items_all DETACH PARTITION content_items_auto")
    op.execute("ALTER TABLE content_items_all DETACH PARTITION content_items")

    # Drop parent table (this drops content_items_all_pkey and content_items_all_uidx_id_src)
    op.execute("DROP TABLE content_items_all")

    # Drop the per-child unique indexes (no longer needed)
    op.execute("DROP INDEX IF EXISTS items_uidx_id_src")
    op.execute("DROP INDEX IF EXISTS auto_uidx_id_src")

    # Original PKs on (id) remain intact - no need to recreate them
