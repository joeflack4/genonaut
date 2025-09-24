"""Utility for managing PostgreSQL wal_buffers setting.

This utility provides functionality to set and reset PostgreSQL's wal_buffers
parameter using ALTER SYSTEM commands. Changes require a PostgreSQL restart
to take effect.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from env/.env
env_file = project_root / "env" / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Fallback to .env in project root
    load_dotenv(project_root / ".env")


logger = logging.getLogger(__name__)


class WalBuffersManager:
    """Manages PostgreSQL wal_buffers setting using ALTER SYSTEM."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)

    def get_current_wal_buffers(self) -> str:
        """Get the current wal_buffers setting."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SHOW wal_buffers"))
                current_value = result.scalar()
                logger.info(f"Current wal_buffers: {current_value}")
                return current_value
        except Exception as e:
            logger.error(f"Failed to get current wal_buffers: {e}")
            raise

    def set_wal_buffers(self, value: str) -> str:
        """Set wal_buffers using ALTER SYSTEM.

        Args:
            value: The wal_buffers value (e.g., '4MB', '64MB')

        Returns:
            The previous wal_buffers value
        """
        try:
            # Get current value before changing
            current_value = self.get_current_wal_buffers()

            # Use autocommit connection for ALTER SYSTEM
            with self.engine.connect() as conn:
                # Set autocommit mode (ALTER SYSTEM cannot run in transaction block)
                conn.execute(text("COMMIT"))  # End any existing transaction
                conn.connection.autocommit = True

                logger.info(f"Setting wal_buffers to {value} using ALTER SYSTEM...")
                conn.execute(text(f"ALTER SYSTEM SET wal_buffers = '{value}'"))

                # Restore normal transaction mode
                conn.connection.autocommit = False

                logger.info(f"wal_buffers successfully changed from {current_value} to {value}")
                logger.warning("⚠️  PostgreSQL restart required for the new wal_buffers setting to take effect!")

                return current_value

        except Exception as e:
            logger.error(f"Failed to set wal_buffers to {value}: {e}")
            raise

    def reset_wal_buffers(self, default_value: str = '4MB') -> str:
        """Reset wal_buffers to the default value.

        Args:
            default_value: The default value to reset to (default: '4MB')

        Returns:
            The previous wal_buffers value
        """
        logger.info(f"Resetting wal_buffers to default value: {default_value}")
        return self.set_wal_buffers(default_value)

    def close(self):
        """Close the database engine."""
        self.engine.dispose()


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def create_cli_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Manage PostgreSQL wal_buffers setting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set wal_buffers to 64MB
  python -m genonaut.db.utils.wal_buffers set --value 64MB --database-url postgresql://user:pass@localhost/db

  # Reset wal_buffers to default (4MB)
  python -m genonaut.db.utils.wal_buffers reset --database-url postgresql://user:pass@localhost/db

  # Show current wal_buffers value
  python -m genonaut.db.utils.wal_buffers show --database-url postgresql://user:pass@localhost/db

Note: All changes require PostgreSQL restart to take effect.
        """
    )

    # Global options
    parser.add_argument('--database-url', type=str, required=True,
                       help='PostgreSQL database URL')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Set command
    set_parser = subparsers.add_parser('set', help='Set wal_buffers to specific value')
    set_parser.add_argument('--value', type=str, required=True,
                           help='wal_buffers value (e.g., 4MB, 64MB, 128MB)')

    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset wal_buffers to default value')
    reset_parser.add_argument('--default', type=str, default='4MB',
                             help='Default value to reset to (default: 4MB)')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show current wal_buffers value')

    return parser


def main():
    """Main entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Set up logging
    setup_logging(args.verbose)

    try:
        # Create wal_buffers manager
        manager = WalBuffersManager(args.database_url)

        if args.command == 'show':
            current_value = manager.get_current_wal_buffers()
            print(f"Current wal_buffers: {current_value}")

        elif args.command == 'set':
            previous_value = manager.set_wal_buffers(args.value)
            print(f"wal_buffers changed from {previous_value} to {args.value}")
            print("⚠️  Please restart PostgreSQL for changes to take effect!")

        elif args.command == 'reset':
            previous_value = manager.reset_wal_buffers(args.default)
            print(f"wal_buffers reset from {previous_value} to {args.default}")
            print("⚠️  Please restart PostgreSQL for changes to take effect!")

        manager.close()

    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()