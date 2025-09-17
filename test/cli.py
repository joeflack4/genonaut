#!/usr/bin/env python3
"""Command-line interface for test database management.

This CLI provides utilities for managing test databases and schemas,
including cleanup of excess test schemas.
"""

import argparse
import os
import sys
from typing import Optional

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the utils module directly
test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, test_dir)
import utils
clear_excess_test_schemas = utils.clear_excess_test_schemas


def get_database_url() -> str:
    """Get database URL from environment variables.
    
    Returns:
        Database URL string
        
    Raises:
        ValueError: If required environment variables are not set
    """
    # Try to get full DATABASE_URL first
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.strip():
        return database_url
    
    # Otherwise, construct from individual components
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    database = os.getenv('DB_NAME', 'genonaut')
    username = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD')
    
    if not password:
        raise ValueError(
            "Database password must be provided via DB_PASSWORD or DATABASE_URL environment variable"
        )
    
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"


def clear_excess_test_schemas_cmd(args) -> None:
    """Command to clear excess test schemas.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        database_url = get_database_url()
        print(f"Connecting to database to clear excess test schemas...")
        
        clear_excess_test_schemas(
            database_url=database_url,
            keep_latest=args.keep_latest
        )
        
        print("Successfully cleared excess test schemas.")
        
    except Exception as e:
        print(f"Error clearing test schemas: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Test database management utilities for Genonaut",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --clear-excess-test-schemas
  %(prog)s --clear-excess-test-schemas --keep-latest 3

Environment Variables:
  DATABASE_URL       Full database connection URL
  DB_HOST           Database host (default: localhost)
  DB_PORT           Database port (default: 5432)  
  DB_NAME           Database name (default: genonaut)
  DB_USER           Database username (default: postgres)
  DB_PASSWORD       Database password (required)
        """
    )
    
    parser.add_argument(
        '--clear-excess-test-schemas',
        action='store_true',
        help='Clear excess test schemas, keeping only the most recent ones'
    )
    
    parser.add_argument(
        '--keep-latest',
        type=int,
        default=1,
        help='Number of most recent test schemas to keep when clearing (default: 1)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Genonaut Test CLI 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.keep_latest < 1:
        parser.error("--keep-latest must be at least 1")
    
    # Execute commands
    if args.clear_excess_test_schemas:
        clear_excess_test_schemas_cmd(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()