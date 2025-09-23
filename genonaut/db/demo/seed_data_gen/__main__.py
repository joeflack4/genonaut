"""Main entry point for synthetic data generation.

This module provides the CLI interface for generating synthetic seed data
for the Genonaut database.
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from urllib.parse import urlparse

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from genonaut.db.utils import get_database_session
from genonaut.db.demo.seed_data_gen.config import ConfigManager
from genonaut.db.demo.seed_data_gen.generator import SyntheticDataGenerator


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('synthetic_data_generation.log')
        ]
    )


def create_cli_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic seed data for Genonaut database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m genonaut.db.demo.seed_data_gen generate
  python -m genonaut.db.demo.seed_data_gen generate --target-rows-users 5000
  python -m genonaut.db.demo.seed_data_gen generate --batch-size-content-items 5000 --max-workers 8
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate synthetic data')

    # Configuration overrides
    gen_parser.add_argument('--batch-size-users', type=int,
                           help='Batch size for user insertion')
    gen_parser.add_argument('--batch-size-content-items', type=int,
                           help='Batch size for content items insertion')
    gen_parser.add_argument('--batch-size-content-items-auto', type=int,
                           help='Batch size for auto content items insertion')
    gen_parser.add_argument('--batch-size-generation-jobs', type=int,
                           help='Batch size for generation jobs insertion')

    gen_parser.add_argument('--target-rows-users', type=int,
                           help='Target number of users to generate')
    gen_parser.add_argument('--target-rows-content-items', type=int,
                           help='Target number of content items to generate')
    gen_parser.add_argument('--target-rows-content-items-auto', type=int,
                           help='Target number of auto content items to generate')

    gen_parser.add_argument('--max-workers', type=int,
                           help='Maximum number of worker processes for prompt generation')
    gen_parser.add_argument('--images-dir', type=str,
                           help='Directory path for image storage')

    gen_parser.add_argument('--database-url', type=str, required=True,
                           help='Database URL (must end with _demo or _test for safety)')

    gen_parser.add_argument('--config', type=str, default='config.json',
                           help='Path to configuration file (default: config.json)')

    gen_parser.add_argument('--verbose', '-v', action='store_true',
                           help='Enable verbose logging')

    return parser


def validate_database_url(database_url: str) -> str:
    """Validate that database URL points to a demo or test database.

    Args:
        database_url: Database URL to validate

    Returns:
        The validated database URL

    Raises:
        ValueError: If database name doesn't end with _demo or _test
    """
    try:
        parsed = urlparse(database_url)
        database_name = parsed.path.lstrip('/')

        if not database_name.endswith(('_demo', '_test')):
            raise ValueError(
                f"Database name '{database_name}' must end with '_demo' or '_test' for safety. "
                f"This prevents accidental data generation in production databases."
            )

        return database_url

    except Exception as e:
        raise ValueError(f"Invalid database URL: {e}")


def main():
    """Main entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()

    if args.command != 'generate':
        parser.print_help()
        sys.exit(1)

    # Set up logging
    setup_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting synthetic data generation CLI")

        # Validate database URL for safety
        validated_database_url = validate_database_url(args.database_url)
        logger.info(f"Using validated database URL: {validated_database_url}")

        # Load configuration
        config_manager = ConfigManager(args.config)

        # Create CLI overrides dictionary
        cli_overrides = {}
        override_mapping = {
            'batch_size_users': args.batch_size_users,
            'batch_size_content_items': args.batch_size_content_items,
            'batch_size_content_items_auto': args.batch_size_content_items_auto,
            'batch_size_generation_jobs': args.batch_size_generation_jobs,
            'target_rows_users': args.target_rows_users,
            'target_rows_content_items': args.target_rows_content_items,
            'target_rows_content_items_auto': args.target_rows_content_items_auto,
            'max_workers': args.max_workers,
            'images_dir': args.images_dir,
        }

        for key, value in override_mapping.items():
            if value is not None:
                cli_overrides[key] = value

        # Get merged configuration
        config = config_manager.get_config(cli_overrides)
        logger.info(f"Configuration loaded: {config}")

        # Validate admin UUID
        admin_uuid = config_manager.validate_admin_uuid(config)
        logger.info(f"Using admin UUID: {admin_uuid}")

        # Get database session using provided URL
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine(validated_database_url, echo=False)
        session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        session = session_factory()
        logger.info("Database session established")

        # Create and run generator
        generator = SyntheticDataGenerator(session, config, admin_uuid)
        generator.generate_all_data()

        print("\nSynthetic data generation completed successfully!")
        logger.info("Synthetic data generation completed successfully")

    except Exception as e:
        logger.error(f"Synthetic data generation failed: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if 'session' in locals():
            session.close()
            logger.info("Database session closed")


if __name__ == '__main__':
    main()