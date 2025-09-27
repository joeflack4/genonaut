"""PostgreSQL extension management for Genonaut database.

This module provides utilities for installing and managing PostgreSQL extensions
required for the Genonaut database schema, particularly for GIN and GiST indexes.
"""

import sys
import argparse
from typing import List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Required PostgreSQL extensions for Genonaut
REQUIRED_EXTENSIONS = [
    'btree_gin',  # For GIN indexes on JSONB
    'pg_trgm',    # For trigram similarity and GiST indexes (CRITICAL for text search)
]


def install_extensions(database_url: str, extensions: Optional[List[str]] = None) -> bool:
    """Install required PostgreSQL extensions.

    First checks if all extensions are already installed. Only installs missing ones.

    Args:
        database_url: PostgreSQL connection URL
        extensions: List of extension names. If None, uses REQUIRED_EXTENSIONS.

    Returns:
        True if all extensions were installed successfully, False otherwise.
    """
    if extensions is None:
        extensions = REQUIRED_EXTENSIONS

    if not database_url or not database_url.startswith('postgresql'):
        print("⚠️  Skipping extension installation (not PostgreSQL)")
        return True

    try:
        engine = create_engine(database_url)

        # First, check which extensions are missing
        missing_extensions = []
        with engine.connect() as conn:
            for extension in extensions:
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM pg_extension WHERE extname = :ext_name"
                ), {"ext_name": extension})

                if result.scalar() == 0:
                    missing_extensions.append(extension)

        # If all extensions are already installed, skip with brief message
        if not missing_extensions:
            print(f"✅ All {len(extensions)} extensions already installed")
            return True

        # Install only missing extensions
        print(f"🔧 Installing {len(missing_extensions)} missing extensions: {', '.join(missing_extensions)}")
        with engine.connect() as conn:
            for extension in missing_extensions:
                try:
                    conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {extension};"))
                    conn.commit()
                    print(f"✅ Extension '{extension}' installed")
                except Exception as e:
                    print(f"❌ Failed to install extension '{extension}': {e}")
                    return False

        print(f"🎉 Successfully installed {len(missing_extensions)} extensions")
        return True

    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def verify_extensions(database_url: str, extensions: Optional[List[str]] = None) -> bool:
    """Verify that required PostgreSQL extensions are installed.

    Args:
        database_url: PostgreSQL connection URL
        extensions: List of extension names. If None, uses REQUIRED_EXTENSIONS.

    Returns:
        True if all extensions are installed, False otherwise.
    """
    if extensions is None:
        extensions = REQUIRED_EXTENSIONS

    if not database_url or not database_url.startswith('postgresql'):
        print("⚠️  Skipping extension verification (not PostgreSQL)")
        return True

    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Check each extension
            for extension in extensions:
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM pg_extension WHERE extname = :ext_name"
                ), {"ext_name": extension})

                count = result.scalar()
                if count == 0:
                    print(f"❌ Extension '{extension}' is NOT installed")
                    return False
                else:
                    print(f"✅ Extension '{extension}' is installed")

            # Verify trigram operator classes are available
            if 'pg_trgm' in extensions:
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM pg_opclass WHERE opcname IN ('gist_trgm_ops', 'gin_trgm_ops')"
                ))
                trgm_ops_count = result.scalar()
                if trgm_ops_count >= 2:
                    print("✅ Trigram operator classes (gist_trgm_ops, gin_trgm_ops) are available")
                else:
                    print(f"❌ Expected 2 trigram operator classes, found {trgm_ops_count}")
                    return False

        print(f"🎉 All {len(extensions)} extensions verified successfully")
        return True

    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """CLI entry point for extension management."""
    parser = argparse.ArgumentParser(
        description="Manage PostgreSQL extensions for Genonaut database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install extensions on demo database
  python -m genonaut.db.schema_extensions install $DATABASE_URL_DEMO

  # Verify extensions are installed
  python -m genonaut.db.schema_extensions verify $DATABASE_URL_DEMO

  # Install specific extensions
  python -m genonaut.db.schema_extensions install $DATABASE_URL_DEMO --extensions pg_trgm btree_gin
        """
    )

    parser.add_argument(
        'command',
        choices=['install', 'verify'],
        help='Command to execute'
    )

    parser.add_argument(
        'database_url',
        help='PostgreSQL database URL'
    )

    parser.add_argument(
        '--extensions',
        nargs='+',
        default=REQUIRED_EXTENSIONS,
        help=f'Extensions to manage (default: {" ".join(REQUIRED_EXTENSIONS)})'
    )

    args = parser.parse_args()

    # Only show detailed header for verify command or when installing missing extensions
    if args.command == 'verify':
        print(f"🔧 {args.command.title()}ing PostgreSQL extensions...")
        print(f"📊 Extensions: {', '.join(args.extensions)}")
        print(f"🔗 Database: {args.database_url.split('@')[-1] if '@' in args.database_url else args.database_url}")
        print()

    if args.command == 'install':
        success = install_extensions(args.database_url, args.extensions)
    elif args.command == 'verify':
        success = verify_extensions(args.database_url, args.extensions)
    else:
        print(f"❌ Unknown command: {args.command}")
        sys.exit(1)

    if success:
        if args.command == 'verify':
            print(f"\n✅ {args.command.title()} completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ {args.command.title()} failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()