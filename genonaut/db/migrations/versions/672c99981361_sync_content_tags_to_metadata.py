"""sync_content_tags_to_metadata

Revision ID: 672c99981361
Revises: 4e6b7255d61e
Create Date: 2025-10-25 02:00:32.899151

This migration:
1. Deduplicates existing item_metadata.tags arrays in content_items and content_items_auto
2. Creates PostgreSQL trigger function to sync content_tags to item_metadata.tags
3. Creates triggers on content_tags table (AFTER INSERT, AFTER DELETE)

The trigger maintains synchronization between the normalized content_tags junction table
and the legacy item_metadata.tags JSONB arrays for backwards compatibility.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '672c99981361'
down_revision: Union[str, Sequence[str], None] = '4e6b7255d61e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: deduplicate tags and create sync triggers."""

    # Step 1: Deduplicate existing item_metadata.tags arrays in content_items
    op.execute("""
        UPDATE content_items
        SET item_metadata = jsonb_set(
            COALESCE(item_metadata, '{}'::jsonb),
            '{tags}',
            (
                SELECT jsonb_agg(DISTINCT tag)
                FROM jsonb_array_elements_text(
                    COALESCE(item_metadata->'tags', '[]'::jsonb)
                ) AS tag
            )
        )
        WHERE item_metadata ? 'tags'
        AND jsonb_array_length(item_metadata->'tags') > 0;
    """)

    # Step 2: Deduplicate existing item_metadata.tags arrays in content_items_auto
    op.execute("""
        UPDATE content_items_auto
        SET item_metadata = jsonb_set(
            COALESCE(item_metadata, '{}'::jsonb),
            '{tags}',
            (
                SELECT jsonb_agg(DISTINCT tag)
                FROM jsonb_array_elements_text(
                    COALESCE(item_metadata->'tags', '[]'::jsonb)
                ) AS tag
            )
        )
        WHERE item_metadata ? 'tags'
        AND jsonb_array_length(item_metadata->'tags') > 0;
    """)

    # Step 3: Create trigger function to sync content_tags to item_metadata
    op.execute("""
        CREATE OR REPLACE FUNCTION sync_content_tags_to_metadata()
        RETURNS TRIGGER AS $BODY$
        DECLARE
            tag_name TEXT;
            target_table TEXT;
        BEGIN
            -- Get the tag name from tags table
            SELECT name INTO tag_name
            FROM tags
            WHERE id = COALESCE(NEW.tag_id, OLD.tag_id);

            -- Determine target table based on content_source
            IF COALESCE(NEW.content_source, OLD.content_source) = 'regular' THEN
                target_table := 'content_items';
            ELSIF COALESCE(NEW.content_source, OLD.content_source) = 'auto' THEN
                target_table := 'content_items_auto';
            ELSE
                -- Unknown content_source, skip
                RETURN COALESCE(NEW, OLD);
            END IF;

            -- Handle INSERT: add tag to item_metadata.tags array
            IF TG_OP = 'INSERT' THEN
                EXECUTE format(
                    'UPDATE %I
                     SET item_metadata = jsonb_set(
                         COALESCE(item_metadata, ''{}''::jsonb),
                         ''{tags}'',
                         COALESCE(item_metadata->''tags'', ''[]''::jsonb) || to_jsonb($1::text),
                         true
                     )
                     WHERE id = $2
                     AND NOT (COALESCE(item_metadata->''tags'', ''[]''::jsonb) @> to_jsonb($1::text))',
                    target_table
                ) USING tag_name, NEW.content_id;

                RETURN NEW;

            -- Handle DELETE: remove tag from item_metadata.tags array
            ELSIF TG_OP = 'DELETE' THEN
                EXECUTE format(
                    'UPDATE %I
                     SET item_metadata = jsonb_set(
                         COALESCE(item_metadata, ''{}''::jsonb),
                         ''{tags}'',
                         (
                             SELECT COALESCE(jsonb_agg(elem), ''[]''::jsonb)
                             FROM jsonb_array_elements_text(
                                 COALESCE(item_metadata->''tags'', ''[]''::jsonb)
                             ) AS elem
                             WHERE elem != $1
                         ),
                         true
                     )
                     WHERE id = $2',
                    target_table
                ) USING tag_name, OLD.content_id;

                RETURN OLD;
            END IF;

            RETURN NULL;
        END;
        $BODY$ LANGUAGE plpgsql;
    """)

    # Step 4: Create AFTER INSERT trigger on content_tags
    op.execute("""
        CREATE TRIGGER content_tags_insert_sync
        AFTER INSERT ON content_tags
        FOR EACH ROW
        EXECUTE FUNCTION sync_content_tags_to_metadata();
    """)

    # Step 5: Create AFTER DELETE trigger on content_tags
    op.execute("""
        CREATE TRIGGER content_tags_delete_sync
        AFTER DELETE ON content_tags
        FOR EACH ROW
        EXECUTE FUNCTION sync_content_tags_to_metadata();
    """)


def downgrade() -> None:
    """Downgrade schema: drop sync triggers and function."""

    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS content_tags_insert_sync ON content_tags;")
    op.execute("DROP TRIGGER IF EXISTS content_tags_delete_sync ON content_tags;")

    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS sync_content_tags_to_metadata();")

    # Note: We do NOT re-duplicate the tags arrays during downgrade
    # as that would be destructive and the deduplicated data is still valid
