"""Backfill script to populate content_tags junction table from UUID arrays.

This script:
1. Reads all content_items and content_items_auto rows with non-empty tags arrays
2. For each content_id and each tag_id in its tags array:
   - Inserts a row into content_tags (content_id, content_source, tag_id)
3. Uses batch inserts for performance
4. Handles duplicates gracefully (ON CONFLICT DO NOTHING)

Usage:
    python -m genonaut.db.utils.backfill_content_tags_junction --env-target local-demo
    python -m genonaut.db.utils.backfill_content_tags_junction --env-target local-test --dry-run
"""

import argparse
import logging
import sys
from typing import List, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from genonaut.db.utils import get_database_url, resolve_database_environment

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_content_tags_from_table(
    session: Session,
    table_name: str,
    content_source: str,
    dry_run: bool = False,
    batch_size: int = 1000
) -> Tuple[int, int]:
    """Backfill content_tags junction table from a content table.

    Args:
        session: Database session
        table_name: Name of content table ('content_items' or 'content_items_auto')
        content_source: Source identifier ('regular' or 'auto')
        dry_run: If True, don't commit changes
        batch_size: Number of rows to insert per batch

    Returns:
        (total_rows_processed, total_tags_inserted)
    """
    logger.info(f"Processing {table_name} (content_source='{content_source}')...")

    # Get all rows with non-empty tags arrays
    query = text(f"""
        SELECT id, tags
        FROM {table_name}
        WHERE tags IS NOT NULL
          AND array_length(tags, 1) > 0
    """)

    result = session.execute(query)
    rows = list(result)

    logger.info(f"Found {len(rows)} rows in {table_name} with tags")

    total_rows_processed = 0
    total_tags_inserted = 0
    batch_values = []

    for row in rows:
        content_id = row.id
        tags = row.tags

        if not tags:
            continue

        total_rows_processed += 1

        # Add each tag as a separate junction table row
        for tag_id in tags:
            batch_values.append({
                'content_id': content_id,
                'content_source': content_source,
                'tag_id': str(tag_id)  # Convert UUID to string for SQL
            })

        # Insert batch when it reaches batch_size
        if len(batch_values) >= batch_size:
            if dry_run:
                logger.info(
                    f"[DRY RUN] Would insert {len(batch_values)} rows into content_tags"
                )
                total_tags_inserted += len(batch_values)
            else:
                # Build VALUES clause for batch insert
                values_placeholders = []
                params_dict = {}
                for i, values in enumerate(batch_values):
                    values_placeholders.append(
                        f"(:content_id_{i}, :content_source_{i}, CAST(:tag_id_{i} AS uuid))"
                    )
                    params_dict[f'content_id_{i}'] = values['content_id']
                    params_dict[f'content_source_{i}'] = values['content_source']
                    params_dict[f'tag_id_{i}'] = values['tag_id']

                insert_query = text(f"""
                    INSERT INTO content_tags (content_id, content_source, tag_id)
                    VALUES {', '.join(values_placeholders)}
                    ON CONFLICT (content_id, content_source, tag_id) DO NOTHING
                """)
                session.execute(insert_query, params_dict)
                session.commit()
                total_tags_inserted += len(batch_values)
                logger.info(
                    f"Inserted {total_tags_inserted} tags from {total_rows_processed} "
                    f"rows in {table_name}..."
                )

            batch_values = []

    # Insert remaining batch
    if batch_values:
        if dry_run:
            logger.info(
                f"[DRY RUN] Would insert final {len(batch_values)} rows into content_tags"
            )
            total_tags_inserted += len(batch_values)
        else:
            # Build VALUES clause for batch insert
            values_placeholders = []
            params_dict = {}
            for i, values in enumerate(batch_values):
                values_placeholders.append(
                    f"(:content_id_{i}, :content_source_{i}, CAST(:tag_id_{i} AS uuid))"
                )
                params_dict[f'content_id_{i}'] = values['content_id']
                params_dict[f'content_source_{i}'] = values['content_source']
                params_dict[f'tag_id_{i}'] = values['tag_id']

            insert_query = text(f"""
                INSERT INTO content_tags (content_id, content_source, tag_id)
                VALUES {', '.join(values_placeholders)}
                ON CONFLICT (content_id, content_source, tag_id) DO NOTHING
            """)
            session.execute(insert_query, params_dict)
            session.commit()
            total_tags_inserted += len(batch_values)

    logger.info(
        f"Completed {table_name}: {total_rows_processed} rows processed, "
        f"{total_tags_inserted} tag relationships inserted"
    )

    return total_rows_processed, total_tags_inserted


def main():
    """Main backfill execution."""
    parser = argparse.ArgumentParser(
        description="Backfill content_tags junction table from UUID arrays"
    )
    parser.add_argument(
        "--env-target",
        required=True,
        help="Environment target (e.g., local-demo, local-test)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Insert batch size (default: 1000)"
    )

    args = parser.parse_args()

    # Resolve environment and get database URL
    environment = resolve_database_environment(environment=args.env_target)
    database_url = get_database_url(environment=environment)

    logger.info(f"Environment: {environment}")
    logger.info(f"Database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Batch size: {args.batch_size}")

    if args.dry_run:
        logger.info("=" * 60)
        logger.info("DRY RUN MODE - No changes will be made")
        logger.info("=" * 60)

    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Process both content tables
        total_rows = 0
        total_tags = 0

        # content_items (regular content)
        rows, tags = backfill_content_tags_from_table(
            session,
            'content_items',
            'regular',
            dry_run=args.dry_run,
            batch_size=args.batch_size
        )
        total_rows += rows
        total_tags += tags

        # content_items_auto (auto-generated content)
        rows, tags = backfill_content_tags_from_table(
            session,
            'content_items_auto',
            'auto',
            dry_run=args.dry_run,
            batch_size=args.batch_size
        )
        total_rows += rows
        total_tags += tags

        # Summary
        logger.info("=" * 60)
        logger.info("BACKFILL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total content items processed: {total_rows}")
        logger.info(f"Total tag relationships inserted: {total_tags}")

        if args.dry_run:
            logger.info("=" * 60)
            logger.info("DRY RUN COMPLETE - No changes were made")
            logger.info("=" * 60)
        else:
            # Verify counts
            verify_query = text("""
                SELECT content_source, COUNT(*) as count
                FROM content_tags
                GROUP BY content_source
            """)
            result = session.execute(verify_query)
            logger.info("Verification - Rows in content_tags by source:")
            for row in result:
                logger.info(f"  {row.content_source}: {row.count}")

            logger.info("=" * 60)
            logger.info("BACKFILL COMPLETE")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during backfill: {e}", exc_info=True)
        session.rollback()
        sys.exit(1)
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
