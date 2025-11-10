"""Database utility functions for Genonaut.

This module provides utility functions for database operations including
URL construction, configuration management, and maintenance helpers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional, Sequence, List, Dict, Set, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine, cast, String
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.attributes import flag_modified


# Load environment variables from .env file in the env/ directory
# Path from genonaut/db/init.py -> project_root/env/.env
env_path = Path(__file__).parent.parent.parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)


def _coerce_bool(value: Optional[str]) -> bool:
    """Convert an environment string to boolean.

    Args:
        value: Raw environment variable value.

    Returns:
        True when the value represents a truthy flag, False otherwise.
    """

    if value is None:
        return False

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_environment(environment: Optional[str]) -> str:
    """Normalize database environment selection.

    Args:
        environment: Optional explicit environment name.

    Returns:
        Canonical environment string: ``dev``, ``demo``, or ``test``.
    """

    if environment:
        candidate = environment.strip().lower()
        if candidate in {"dev", "demo", "test"}:
            return candidate

    # Try GENONAUT_DB_ENVIRONMENT first, then extract from ENV_TARGET
    explicit = os.getenv("GENONAUT_DB_ENVIRONMENT")
    if not explicit:
        env_target = os.getenv("ENV_TARGET")
        if env_target:
            # Extract environment type from ENV_TARGET (e.g., 'local-dev' -> 'dev')
            if "-" in env_target:
                explicit = env_target.split("-")[-1]
            else:
                explicit = env_target

    if explicit:
        lowered = explicit.strip().lower()
        if lowered in {"dev", "demo", "test", "prod"}:
            return lowered

    if _coerce_bool(os.getenv("TEST", "0")):
        return "test"
    return "dev"


def resolve_database_environment(
    environment: Optional[str] = None,
) -> str:
    """Public helper to resolve the active database environment."""

    return _normalize_environment(environment)


def _database_name_for_environment(environment: str) -> str:
    """Resolve database name for the requested environment."""

    if environment == "demo":
        return os.getenv("DB_NAME_DEMO", "genonaut_demo")
    if environment == "test":
        return os.getenv("DB_NAME_TEST", "genonaut_test")
    return os.getenv("DB_NAME", "genonaut")


def get_database_url(environment: Optional[str] = None) -> str:
    """Get database URL from environment variables.

    Args:
        environment: Explicit environment name (``dev``, ``demo``, ``test``).

    For initialization tasks, uses admin credentials by default.

    Returns:
        Database URL string.

    Raises:
        ValueError: If required environment variables are not set.
    """

    resolved_environment = _normalize_environment(environment)
    # print(f"get_database_url resolved_environment: {resolved_environment}")
    database_name = _database_name_for_environment(resolved_environment)

    # Prefer an explicit DATABASE_URL variable when provided
    env_key_map = {
        "dev": "DATABASE_URL",
        "demo": "DATABASE_URL_DEMO",
        "test": "DATABASE_URL_TEST",
    }
    url_env_key = env_key_map.get(resolved_environment, "DATABASE_URL")
    raw_url = os.getenv(url_env_key)

    if raw_url and raw_url.strip():
        return raw_url.strip()

    # Otherwise, construct from individual components using admin credentials by default
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")

    # Try admin credentials first (for initialization)
    admin_password = os.getenv("DB_PASSWORD_ADMIN")
    if admin_password:
        return (
            f"postgresql://genonaut_admin:{admin_password}@{host}:{port}/{database_name}"
        )

    # Fall back to legacy credentials for backward compatibility
    username = os.getenv("DB_USER_FOR_INIT", "postgres")
    password = os.getenv("DB_PASSWORD_FOR_INIT")

    if not password:
        raise ValueError(
            "Database password must be provided via DB_PASSWORD_ADMIN (preferred) or "
            "DB_PASSWORD/DATABASE_URL environment variable"
        )

    return f"postgresql://{username}:{password}@{host}:{port}/{database_name}"


def _ensure_allowed_database(name: str, allowed_suffixes: Sequence[str]) -> None:
    """Validate that the database name matches one of the allowed suffixes."""

    if not name:
        raise ValueError("Unable to determine database name for reset operation")

    if not any(name.endswith(suffix) for suffix in allowed_suffixes):
        suffix_list = ", ".join(allowed_suffixes)
        raise ValueError(
            f"Refusing to reset database '{name}'. Allowed suffixes: {suffix_list}."
        )


def _ensure_seed_utilities_importable() -> None:
    """Make sure test database utilities are available for initialization seeding."""

    project_root = Path(__file__).resolve().parent.parent.parent
    candidate_dirs = [
        project_root / "test",
        project_root / "test" / "db",
        Path.cwd() / "test",
        Path.cwd() / "test" / "db",
    ]

    for path in candidate_dirs:
        if path.exists():
            path_str = str(path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)


def get_database_session(environment: Optional[str] = None) -> Session:
    """Create a database session for CLI/standalone usage.

    Args:
        environment: Database environment (dev, demo, test). Defaults to current environment.

    Returns:
        SQLAlchemy Session instance.
    """
    database_url = get_database_url(environment)
    engine = create_engine(database_url, echo=False)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return session_factory()


def get_image_metadata(image_id: int, environment: Optional[str] = None) -> None:
    """Retrieve and pretty-print metadata for a content item.

    Args:
        image_id: The ID of the content item to query.
        environment: Database environment (dev, demo, test). Defaults to current environment.

    Raises:
        SystemExit: If image not found or database error occurs.
    """
    import json
    from sqlalchemy import text

    session = None
    try:
        session = get_database_session(environment)

        # Query for the item_metadata field from content_items_all view
        # Using raw SQL to access the view directly
        query = text("""
            SELECT item_metadata
            FROM content_items_all
            WHERE id = :image_id
        """)

        result = session.execute(query, {"image_id": image_id})
        row = result.fetchone()

        if row is None:
            print(f"Error: No content item found with ID {image_id}")
            sys.exit(1)

        metadata = row[0] if row[0] is not None else {}

        # Pretty print the metadata
        print(json.dumps(metadata, indent=2))

    except Exception as e:
        print(f"Error retrieving metadata: {e}")
        sys.exit(1)
    finally:
        if session is not None:
            session.close()


def _calculate_md5(file_path: Path) -> str:
    """Calculate MD5 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        MD5 hash as hexadecimal string
    """
    md5 = hashlib.md5()
    # Use 1MB chunks for faster I/O
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            md5.update(chunk)
    return md5.hexdigest()


def sync_models_from_fs(environment: Optional[str] = None) -> None:
    """Sync model records in database with files on filesystem.

    Scans the configured ComfyUI models directories for checkpoint and LoRA files,
    then synchronizes the database records with what exists on disk. Handles path
    changes, file renames, and new models.

    Args:
        environment: Database environment (dev, demo, test). Defaults to demo.

    Logic:
        1. Scan filesystem for models matching configured file extensions
        2. For each model file:
           - First check for path match in database
           - If path matches but MD5 differs: mark old record as unresolved, create new record
           - If path matches and MD5 matches/missing: update MD5 and set path_resolves=True
           - If no path match, check for MD5 match (file may have moved)
           - If MD5 matches (single match): update path/filename/name
           - If no matches: insert new record
        3. Mark all unmatched database records as path_resolves=False
        4. Report unrecognized files and imported models
    """
    from genonaut.api.config import get_settings
    from genonaut.db.schema import CheckpointModel, LoraModel

    env = environment or "demo"
    session = None

    try:
        # Get settings and session
        settings = get_settings()
        session = get_database_session(env)

        # Expand user dir and validate paths
        models_dir = Path(settings.comfyui_models_dir).expanduser()
        checkpoints_dir = models_dir / "checkpoints"
        loras_dir = models_dir / "loras"

        if not models_dir.exists():
            print(f"Error: Models directory does not exist: {models_dir}")
            sys.exit(1)

        print(f"Syncing models from: {models_dir}")
        print(f"  Checkpoints: {checkpoints_dir}")
        print(f"  LoRAs: {loras_dir}")
        print()

        # Get file extensions from config
        checkpoint_exts = settings.model_file_extensions_checkpoints
        lora_exts = settings.model_file_extensions_loras

        # Process checkpoints
        print("Processing checkpoints...")
        checkpoint_stats = _sync_model_type(
            session=session,
            model_class=CheckpointModel,
            models_dir=checkpoints_dir,
            base_dir=models_dir,
            valid_extensions=checkpoint_exts,
            model_type="checkpoint"
        )

        # Process LoRAs
        print("\nProcessing LoRAs...")
        lora_stats = _sync_model_type(
            session=session,
            model_class=LoraModel,
            models_dir=loras_dir,
            base_dir=models_dir,
            valid_extensions=lora_exts,
            model_type="lora"
        )

        # Commit all changes
        session.commit()

        # Print summary
        print("\n" + "=" * 80)
        print("SYNC SUMMARY")
        print("=" * 80)
        print(f"\nCheckpoints:")
        print(f"  Added: {checkpoint_stats['added']}")
        print(f"  Updated: {checkpoint_stats['updated']}")
        print(f"  Unresolved: {checkpoint_stats['unresolved']}")
        print(f"  Unrecognized files: {len(checkpoint_stats['unrecognized'])}")

        print(f"\nLoRAs:")
        print(f"  Added: {lora_stats['added']}")
        print(f"  Updated: {lora_stats['updated']}")
        print(f"  Unresolved: {lora_stats['unresolved']}")
        print(f"  Unrecognized files: {len(lora_stats['unrecognized'])}")

        # Print unrecognized files
        all_unrecognized = checkpoint_stats['unrecognized'] + lora_stats['unrecognized']
        if all_unrecognized:
            print(f"\n\nUnrecognized files (not matching configured extensions):")
            for file_path in sorted(all_unrecognized):
                print(f"  {file_path}")

        # Print imported models
        all_imported = checkpoint_stats['imported'] + lora_stats['imported']
        if all_imported:
            print(f"\n\nImported models ({len(all_imported)} total):")
            for name in sorted(all_imported):
                print(f"  {name}")

            print("\n" + "-" * 80)
            print("Next steps for populating metadata:")
            print("  1. Run: make sync-models-export-csv")
            print("  2. Edit the exported CSV to update model metadata")
            print("  3. Run: make sync-models-import-csv")
            print("  (Note: These commands will be implemented separately)")
            print("-" * 80)

        print("\nSync completed successfully!")

    except Exception as e:
        if session:
            session.rollback()
        print(f"\nError during sync: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if session:
            session.close()


def _sync_model_type(
    session: Session,
    model_class: type,
    models_dir: Path,
    base_dir: Path,
    valid_extensions: List[str],
    model_type: str
) -> Dict[str, any]:
    """Sync a specific type of model (checkpoint or LoRA).

    Args:
        session: Database session
        model_class: CheckpointModel or LoraModel class
        models_dir: Directory containing this model type
        base_dir: Base models directory for calculating relative paths
        valid_extensions: List of valid file extensions
        model_type: "checkpoint" or "lora" for logging

    Returns:
        Dictionary with statistics: added, updated, unresolved, unrecognized, imported
    """
    stats = {
        'added': 0,
        'updated': 0,
        'unresolved': 0,
        'unrecognized': [],
        'imported': []
    }

    # Track which database records we've touched
    touched_ids: Set[str] = set()

    # Load all existing records into memory for faster lookups
    print(f"  Loading existing {model_type} records from database...")
    all_records = session.query(model_class).all()

    # Build lookup dictionaries for faster access
    records_by_path: Dict[str, any] = {}
    records_by_md5: Dict[str, List[any]] = {}

    for record in all_records:
        records_by_path[record.path] = record

        # Build MD5 lookup if MD5 exists in metadata
        metadata = record.model_metadata or {}
        if 'md5' in metadata and metadata['md5']:
            md5_val = metadata['md5']
            if md5_val not in records_by_md5:
                records_by_md5[md5_val] = []
            records_by_md5[md5_val].append(record)

    print(f"  Found {len(all_records)} existing records in database")

    # Scan filesystem for model files
    file_paths: List[Path] = []
    if models_dir.exists():
        for file_path in models_dir.rglob('*'):
            if file_path.is_file():
                file_paths.append(file_path)

    print(f"  Found {len(file_paths)} files in {models_dir}")

    # Process each file
    for file_path in file_paths:
        # Check if extension is valid
        if file_path.suffix.lower() not in valid_extensions:
            stats['unrecognized'].append(str(file_path))
            continue

        # Calculate relative path from base models directory
        try:
            rel_path = file_path.relative_to(base_dir)
        except ValueError:
            print(f"Warning: File outside base directory: {file_path}")
            continue

        rel_path_str = str(rel_path)
        filename = file_path.name
        name = file_path.stem  # filename without extension

        # Calculate MD5 hash
        try:
            md5_hash = _calculate_md5(file_path)
        except Exception as e:
            print(f"Warning: Failed to calculate MD5 for {file_path}: {e}")
            continue

        # Try to find matching record
        # First, check for path match
        existing_by_path = records_by_path.get(rel_path_str)

        if existing_by_path:
            # Path matches - check MD5
            existing_metadata = existing_by_path.model_metadata or {}
            existing_md5 = existing_metadata.get('md5')

            if existing_md5 and existing_md5 != md5_hash:
                # MD5 mismatch - mark old as unresolved and create new
                print(f"  MD5 mismatch for {rel_path_str}: marking old record as unresolved")

                # Prepend "unresolved/" to existing record's path
                existing_by_path.path = f"unresolved/{existing_by_path.path}"
                existing_metadata['path_resolves'] = False
                existing_by_path.model_metadata = existing_metadata
                flag_modified(existing_by_path, 'model_metadata')
                stats['unresolved'] += 1

                # Create new record for the file we found
                new_metadata = {'md5': md5_hash, 'path_resolves': True}
                new_record = model_class(
                    path=rel_path_str,
                    filename=filename,
                    name=name,
                    model_metadata=new_metadata
                )
                session.add(new_record)
                touched_ids.add(str(new_record.id))
                stats['added'] += 1
                stats['imported'].append(name)
                print(f"  Added new record for {rel_path_str}")
            else:
                # Path matches and (MD5 matches or doesn't exist)
                existing_metadata['md5'] = md5_hash
                existing_metadata['path_resolves'] = True
                existing_by_path.model_metadata = existing_metadata
                flag_modified(existing_by_path, 'model_metadata')
                touched_ids.add(str(existing_by_path.id))
                stats['updated'] += 1
                print(f"  Updated {rel_path_str}")
        else:
            # No path match - check for MD5 match (file may have moved)
            md5_matches = records_by_md5.get(md5_hash, [])

            if len(md5_matches) > 1:
                print(f"Error: Multiple MD5 matches for {rel_path_str}")
                sys.exit(1)
            elif len(md5_matches) == 1:
                # Single MD5 match - update the record
                record = md5_matches[0]
                print(f"  File moved: {record.path} -> {rel_path_str}")

                record.path = rel_path_str
                record.filename = filename
                record.name = name
                metadata = record.model_metadata or {}
                metadata['path_resolves'] = True
                record.model_metadata = metadata
                flag_modified(record, 'model_metadata')
                touched_ids.add(str(record.id))
                stats['updated'] += 1
            else:
                # No match - insert new record
                new_metadata = {'md5': md5_hash, 'path_resolves': True}
                new_record = model_class(
                    path=rel_path_str,
                    filename=filename,
                    name=name,
                    model_metadata=new_metadata
                )
                session.add(new_record)
                touched_ids.add(str(new_record.id))
                stats['added'] += 1
                stats['imported'].append(name)
                print(f"  Added {rel_path_str}")

    # Mark untouched records as unresolved
    for record in all_records:
        if str(record.id) not in touched_ids:
            metadata = record.model_metadata or {}
            # Only update if not already marked as unresolved
            if metadata.get('path_resolves') != False:
                metadata['path_resolves'] = False
                record.model_metadata = metadata
                flag_modified(record, 'model_metadata')
                print(f"  Marked as unresolved: {record.path}")
                stats['unresolved'] += 1

    return stats


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Entry point for the module's CLI interface."""
    parser = argparse.ArgumentParser(
        description="Database utility functions for Genonaut",
    )

    parser.add_argument(
        "--get-database-url",
        action="store_true",
        help="Print the database URL for the current environment"
    )

    parser.add_argument(
        "--get-image-metadata",
        type=int,
        metavar="IMG_ID",
        help="Retrieve and display metadata for a content item by ID"
    )

    parser.add_argument(
        "--sync-models-from-fs",
        action="store_true",
        help="Sync model records in database with files on filesystem"
    )

    parser.add_argument(
        "--environment",
        "-e",
        choices=("dev", "demo", "test"),
        help="Target database environment (defaults to demo)",
    )

    args = parser.parse_args(argv)

    if args.get_database_url:
        try:
            url = get_database_url(environment=args.environment)
            print(url)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    elif args.get_image_metadata is not None:
        # Default to demo environment if not specified
        env = args.environment or "demo"
        get_image_metadata(args.get_image_metadata, environment=env)
    elif args.sync_models_from_fs:
        # Default to demo environment if not specified
        env = args.environment or "demo"
        sync_models_from_fs(environment=env)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
