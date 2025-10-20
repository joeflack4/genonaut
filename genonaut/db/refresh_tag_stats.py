#!/usr/bin/env python3
"""Refresh tag cardinality statistics.

This script populates the tag_cardinality_stats table by computing
the number of distinct content items per (tag_id, content_source) pair.

Used by the tag query planner to select optimal query strategies.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from genonaut.api.repositories.tag_repository import TagRepository
from genonaut.config_loader import construct_database_url


def main():
    """Refresh tag cardinality statistics."""
    # Get database credentials from environment
    db_password = os.getenv("DB_PASSWORD_ADMIN")
    if not db_password:
        print("Error: DB_PASSWORD_ADMIN environment variable not set")
        sys.exit(1)

    db_user = os.getenv("DB_USER_ADMIN", "genonaut_admin")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "genonaut_demo")

    # Construct database URL
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    print(f"Connecting to database: {db_name} at {db_host}")

    # Create engine and session
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Create repository and refresh stats
        print("Refreshing tag cardinality statistics...")
        repo = TagRepository(db)
        count = repo.refresh_tag_cardinality_stats()

        print(f"✅ Successfully refreshed {count} tag-source cardinality stats")

        # Show sample of results
        print("\nSample of stats (first 10):")
        from genonaut.db.schema import TagCardinalityStats, Tag

        stats = (
            db.query(TagCardinalityStats, Tag.name)
            .join(Tag, TagCardinalityStats.tag_id == Tag.id)
            .order_by(TagCardinalityStats.cardinality.desc())
            .limit(10)
            .all()
        )

        for stat, tag_name in stats:
            print(f"  {tag_name:30s} | {stat.content_source:10s} | {stat.cardinality:8d} items")

    except Exception as e:
        print(f"❌ Error refreshing stats: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
