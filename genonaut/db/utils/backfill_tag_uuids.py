"""Backfill script to convert tag names in tags_old to UUID arrays in tags column.

This script:
1. Reads all content_items and content_items_auto rows
2. For each tag name in tags_old (JSONB array of strings)
3. Looks up the corresponding UUID from the tags table
4. Updates the tags column (UUID array) with the found UUIDs
5. Logs warnings for any missing tags

Usage:
    python -m genonaut.db.utils.backfill_tag_uuids --env-target local-demo
    python -m genonaut.db.utils.backfill_tag_uuids --env-target local-test --dry-run
"""

import argparse
import logging
import sys
from typing import Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from genonaut.db.utils import get_database_url, resolve_database_environment

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_tag_name_to_uuid_mapping(session: Session) -> Dict[str, UUID]:
    """Load mapping of tag names to UUIDs from tags table."""
    logger.info("Loading tag name to UUID mapping from tags table...")

    result = session.execute(text("SELECT id, name FROM tags"))
    mapping = {row.name: row.id for row in result}

    logger.info(f"Loaded {len(mapping)} tags from tags table")
    return mapping


def backfill_content_table(
    session: Session,
    table_name: str,
    tag_mapping: Dict[str, UUID],
    dry_run: bool = False
) -> tuple[int, int, Set[str]]:
    """Backfill tags column for a content table.

    Returns:
        (rows_updated, rows_with_tags, missing_tags)
    """
    logger.info(f"Processing {table_name}...")

    # Get all rows with non-empty tags_old
    query = text(f"""
        SELECT id, tags_old
        FROM {table_name}
        WHERE tags_old IS NOT NULL
          AND tags_old != 'null'::jsonb
          AND jsonb_array_length(tags_old) > 0
    """)

    result = session.execute(query)
    rows = list(result)

    logger.info(f"Found {len(rows)} rows in {table_name} with tags_old data")

    rows_updated = 0
    rows_with_tags = 0
    missing_tags: Set[str] = set()

    for row in rows:
        content_id = row.id
        tags_old = row.tags_old

        if not tags_old:
            continue

        rows_with_tags += 1

        # Convert tag names to UUIDs
        tag_uuids: List[UUID] = []
        for tag_name in tags_old:
            if not isinstance(tag_name, str):
                logger.warning(
                    f"{table_name} id={content_id}: "
                    f"Skipping non-string tag: {tag_name} (type={type(tag_name)})"
                )
                continue

            tag_uuid = tag_mapping.get(tag_name)
            if tag_uuid:
                tag_uuids.append(tag_uuid)
            else:
                missing_tags.add(tag_name)
                logger.warning(
                    f"{table_name} id={content_id}: "
                    f"Tag '{tag_name}' not found in tags table"
                )

        # Update tags column with UUID array
        if tag_uuids:
            if dry_run:
                logger.info(
                    f"[DRY RUN] Would update {table_name} id={content_id}: "
                    f"{len(tags_old)} tag names -> {len(tag_uuids)} UUIDs"
                )
            else:
                # Use ARRAY constructor to build UUID array from strings
                update_query = text(f"""
                    UPDATE {table_name}
                    SET tags = ARRAY(
                        SELECT unnest(:tag_array)::uuid
                    )
                    WHERE id = :content_id
                """)
                uuid_strings = [str(uuid) for uuid in tag_uuids]
                session.execute(
                    update_query,
                    {"tag_array": uuid_strings, "content_id": content_id}
                )
                rows_updated += 1

                if rows_updated % 1000 == 0:
                    logger.info(f"Updated {rows_updated} rows in {table_name}...")
                    if not dry_run:
                        session.commit()

    if not dry_run:
        session.commit()

    logger.info(
        f"Completed {table_name}: {rows_updated} rows updated, "
        f"{rows_with_tags} total rows with tags, "
        f"{len(missing_tags)} unique missing tags"
    )

    return rows_updated, rows_with_tags, missing_tags


def main():
    """Main backfill execution."""
    parser = argparse.ArgumentParser(
        description="Backfill tag UUIDs from tag names"
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
        help="Commit after this many updates (default: 1000)"
    )

    args = parser.parse_args()

    # Resolve environment and get database URL
    environment = resolve_database_environment(environment=args.env_target)
    database_url = get_database_url(environment=environment)

    logger.info(f"Environment: {environment}")
    logger.info(f"Database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    logger.info(f"Dry run: {args.dry_run}")

    if args.dry_run:
        logger.info("=" * 60)
        logger.info("DRY RUN MODE - No changes will be made")
        logger.info("=" * 60)

    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Load tag mapping
        tag_mapping = load_tag_name_to_uuid_mapping(session)

        if not tag_mapping:
            logger.error("No tags found in tags table! Cannot proceed.")
            sys.exit(1)

        # Backfill both tables
        all_missing_tags: Set[str] = set()
        total_updated = 0
        total_with_tags = 0

        for table_name in ['content_items', 'content_items_auto']:
            updated, with_tags, missing = backfill_content_table(
                session, table_name, tag_mapping, dry_run=args.dry_run
            )
            total_updated += updated
            total_with_tags += with_tags
            all_missing_tags.update(missing)

        # Summary
        logger.info("=" * 60)
        logger.info("BACKFILL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total rows with tags: {total_with_tags}")
        logger.info(f"Total rows updated: {total_updated}")
        logger.info(f"Unique missing tags: {len(all_missing_tags)}")

        if all_missing_tags:
            logger.warning("Missing tags:")
            for tag_name in sorted(all_missing_tags):
                logger.warning(f"  - {tag_name}")

        if args.dry_run:
            logger.info("=" * 60)
            logger.info("DRY RUN COMPLETE - No changes were made")
            logger.info("=" * 60)
        else:
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
