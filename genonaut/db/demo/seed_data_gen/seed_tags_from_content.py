"""Seed tags table from existing content tags.

This script extracts all unique tag names from content_items and content_items_auto
tables (from tags_old JSONB fields) and populates the tags table with them.

This is an ad-hoc migration script for converting from JSONB tag arrays to the
normalized tags table with UUID foreign keys.

Usage:
    python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target demo
    python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target demo --clear-existing
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from typing import Set
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from genonaut.db.utils import get_database_url, resolve_database_environment

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_unique_tags(session) -> Set[str]:
    """Extract all unique tag names from content tables.

    Returns:
        Set of unique tag name strings
    """
    logger.info("Extracting unique tags from content_items and content_items_auto...")

    unique_tags: Set[str] = set()

    for table_name in ['content_items', 'content_items_auto']:
        query = text(f"""
            SELECT DISTINCT jsonb_array_elements_text(tags_old) as tag_name
            FROM {table_name}
            WHERE tags_old IS NOT NULL
              AND tags_old != 'null'::jsonb
              AND jsonb_array_length(tags_old) > 0
        """)

        result = session.execute(query)
        table_tags = {row.tag_name for row in result if row.tag_name}
        unique_tags.update(table_tags)

        logger.info(f"Found {len(table_tags)} unique tags in {table_name}")

    logger.info(f"Total unique tags across all tables: {len(unique_tags)}")
    return unique_tags


def clear_tags_table(session) -> None:
    """Clear all rows from tags table and related tables.

    This will cascade delete to tag_parents and tag_ratings due to foreign keys.
    """
    logger.info("Clearing existing tags (this will cascade to tag_parents and tag_ratings)...")

    # Delete in order due to foreign key constraints
    session.execute(text("DELETE FROM tag_ratings"))
    session.execute(text("DELETE FROM tag_parents"))
    session.execute(text("DELETE FROM tags"))
    session.commit()

    logger.info("Cleared all existing tags")


def insert_tags(session, tag_names: Set[str]) -> int:
    """Insert tag names into tags table with generated UUIDs.

    Args:
        session: Database session
        tag_names: Set of unique tag name strings

    Returns:
        Number of tags inserted
    """
    logger.info(f"Inserting {len(tag_names)} tags into tags table...")

    now = datetime.utcnow()
    inserted = 0

    for tag_name in sorted(tag_names):
        tag_id = uuid4()
        insert_query = text("""
            INSERT INTO tags (id, name, tag_metadata, created_at, updated_at)
            VALUES (:id, :name, :metadata, :created_at, :updated_at)
        """)

        session.execute(
            insert_query,
            {
                "id": tag_id,
                "name": tag_name,
                "metadata": json.dumps({}),
                "created_at": now,
                "updated_at": now
            }
        )

        inserted += 1
        if inserted % 100 == 0:
            logger.info(f"Inserted {inserted} tags...")
            session.commit()

    session.commit()
    logger.info(f"Successfully inserted {inserted} tags")
    return inserted


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Seed tags table from content tags_old fields"
    )
    parser.add_argument(
        "--env-target",
        required=True,
        help="Environment target (e.g., demo, test)"
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Clear existing tags before inserting new ones"
    )

    args = parser.parse_args()

    # Resolve environment and get database URL
    environment = resolve_database_environment(environment=args.env_target)
    database_url = get_database_url(environment=environment)

    logger.info(f"Environment: {environment}")
    logger.info(f"Database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    logger.info(f"Clear existing: {args.clear_existing}")

    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Clear existing tags if requested
        if args.clear_existing:
            clear_tags_table(session)

        # Extract unique tags from content
        unique_tags = extract_unique_tags(session)

        if not unique_tags:
            logger.warning("No tags found in content tables!")
            sys.exit(0)

        # Insert tags
        inserted = insert_tags(session, unique_tags)

        # Summary
        logger.info("=" * 60)
        logger.info("SEED TAGS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Unique tags found: {len(unique_tags)}")
        logger.info(f"Tags inserted: {inserted}")
        logger.info("=" * 60)
        logger.info("COMPLETE - Tags table populated from content")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during tag seeding: {e}", exc_info=True)
        session.rollback()
        sys.exit(1)
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
