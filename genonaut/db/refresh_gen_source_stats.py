#!/usr/bin/env python3
"""Refresh generation source statistics.

This script populates the gen_source_stats table by computing
the number of content items per (user_id, source_type) pair,
as well as community-wide totals.

Used by the gallery UI to quickly display content counts.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.config_loader import construct_database_url


def main():
    """Refresh generation source statistics."""
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
        print("Refreshing generation source statistics...")
        repo = ContentRepository(db)
        count = repo.refresh_gen_source_stats()

        print(f"Successfully refreshed {count} generation source stats")

        # Show sample of results
        print("\nSample of stats (first 10):")
        from genonaut.db.schema import GenSourceStats, User

        stats = (
            db.query(GenSourceStats, User.username)
            .outerjoin(User, GenSourceStats.user_id == User.id)
            .order_by(GenSourceStats.count.desc())
            .limit(10)
            .all()
        )

        for stat, username in stats:
            user_label = username if username else "Community"
            print(f"  {user_label:30s} | {stat.source_type:10s} | {stat.count:8d} items")

    except Exception as e:
        print(f"Error refreshing stats: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
