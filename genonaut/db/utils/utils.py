"""Database utility functions for Genonaut.

This module provides utility functions for database operations including
URL construction, configuration management, and maintenance helpers.
"""

from __future__ import annotations

import argparse
import csv
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
            base_dir=checkpoints_dir,
            valid_extensions=checkpoint_exts,
            model_type="checkpoint"
        )

        # Process LoRAs
        print("\nProcessing LoRAs...")
        lora_stats = _sync_model_type(
            session=session,
            model_class=LoraModel,
            models_dir=loras_dir,
            base_dir=loras_dir,
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
        print(f"  Unchanged (already up-to-date): {checkpoint_stats['unchanged']}")
        print(f"  Unresolved: {checkpoint_stats['unresolved']}")
        print(f"  Unrecognized files: {len(checkpoint_stats['unrecognized'])}")

        print(f"\nLoRAs:")
        print(f"  Added: {lora_stats['added']}")
        print(f"  Updated: {lora_stats['updated']}")
        print(f"  Unchanged (already up-to-date): {lora_stats['unchanged']}")
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
        'unchanged': 0,
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
                # Check if update is actually needed
                needs_update = False
                if existing_metadata.get('md5') != md5_hash:
                    existing_metadata['md5'] = md5_hash
                    needs_update = True
                if existing_metadata.get('path_resolves') != True:
                    existing_metadata['path_resolves'] = True
                    needs_update = True

                touched_ids.add(str(existing_by_path.id))

                if needs_update:
                    existing_by_path.model_metadata = existing_metadata
                    flag_modified(existing_by_path, 'model_metadata')
                    stats['updated'] += 1
                    print(f"  Updated {rel_path_str}")
                else:
                    stats['unchanged'] += 1
        else:
            # No path match - check for MD5 match (file may have moved)
            md5_matches = records_by_md5.get(md5_hash, [])

            if len(md5_matches) > 1:
                print(f"Error: Multiple MD5 matches for {rel_path_str}")
                print(f"  MD5: {md5_hash}")
                print(f"  Matching records:")
                for record in md5_matches:
                    print(f"    - {record.path}")
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


def _has_critical_nulls_checkpoint(checkpoint: any) -> bool:
    """Check if a checkpoint model has any critical null fields.

    Critical fields for checkpoints:
    - architecture
    - model_metadata

    Args:
        checkpoint: CheckpointModel instance

    Returns:
        True if any critical field is null/empty, False otherwise
    """
    # Check architecture
    if not checkpoint.architecture or not checkpoint.architecture.strip():
        return True

    # Check model_metadata (should not be None or empty dict)
    if not checkpoint.model_metadata or len(checkpoint.model_metadata) == 0:
        return True

    return False


def _has_critical_nulls_lora(lora: any) -> bool:
    """Check if a LoRA model has any critical null fields.

    Critical fields for LoRAs:
    - compatible_architectures
    - family
    - trigger_words
    - model_metadata

    Args:
        lora: LoraModel instance

    Returns:
        True if any critical field is null/empty, False otherwise
    """
    # Check compatible_architectures
    if not lora.compatible_architectures or not lora.compatible_architectures.strip():
        return True

    # Check family
    if not lora.family or not lora.family.strip():
        return True

    # Check trigger_words (should not be None or empty list)
    # Exception: If model_metadata.has_no_trigger_words is True, skip this check
    has_no_trigger_words = (
        lora.model_metadata
        and isinstance(lora.model_metadata, dict)
        and lora.model_metadata.get('has_no_trigger_words') is True
    )
    if not has_no_trigger_words:
        if not lora.trigger_words or len(lora.trigger_words) == 0:
            return True

    # Check optimal_checkpoints (should not be None or empty list)
    # - note: If reactivate this, add field to list in docstring
    # if not lora.optimal_checkpoints or len(lora.optimal_checkpoints) == 0:
    #     return True

    # Check model_metadata (should not be None or empty dict)
    if not lora.model_metadata or len(lora.model_metadata) == 0:
        return True

    return False


def export_models_to_csv(
    output_dir: Optional[str] = None,
    environment: Optional[str] = None,
    only_critical_nulls: bool = False
) -> None:
    """Export model metadata to CSV files.

    Creates two CSV files (checkpoints.csv and loras.csv) with model metadata
    for easy editing and management. By default, exports to io/output/ directory.

    Args:
        output_dir: Directory to write CSV files (defaults to io/output/)
        environment: Database environment (dev, demo, test). Defaults to demo.
        only_critical_nulls: If True, only export records with critical null fields
                            (checkpoint: architecture, model_metadata)
                            (lora: compatible_architectures, family, trigger_words,
                             optimal_checkpoints, model_metadata)

    The CSV files will contain all metadata fields for each model type:
    - Checkpoints: path, name, version, architecture, family, description, tags, model_metadata
    - LoRAs: path, name, version, compatible_architectures, family, description, tags,
             trigger_words, optimal_checkpoints, model_metadata
    """
    from genonaut.db.schema import CheckpointModel, LoraModel

    env = environment or "demo"
    session = None

    try:
        # Determine output directory
        if output_dir is None:
            # Go up from genonaut/db/utils/utils.py to project root
            project_root = Path(__file__).parent.parent.parent.parent
            output_path = project_root / "io" / "output"
        else:
            output_path = Path(output_dir)

        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"Exporting model metadata to: {output_path}")

        # Get database session
        session = get_database_session(env)

        # Export checkpoints
        checkpoints_csv = output_path / "checkpoints.csv"
        checkpoint_fields = [
            'path', 'name', 'version', 'architecture', 'family',
            'description', 'tags', 'model_metadata'
        ]

        print(f"\nExporting checkpoints...")
        checkpoints = session.query(CheckpointModel).order_by(CheckpointModel.name).all()

        # Filter if only_critical_nulls is True
        if only_critical_nulls:
            checkpoints = [c for c in checkpoints if _has_critical_nulls_checkpoint(c)]
            print(f"  Filtering to only records with critical null fields...")

        with open(checkpoints_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=checkpoint_fields)
            writer.writeheader()

            for checkpoint in checkpoints:
                row = {
                    'path': checkpoint.path or '',
                    'name': checkpoint.name or '',
                    'version': checkpoint.version or '',
                    'architecture': checkpoint.architecture or '',
                    'family': checkpoint.family or '',
                    'description': checkpoint.description or '',
                    'tags': json.dumps(checkpoint.tags or []),
                    'model_metadata': json.dumps(checkpoint.model_metadata or {})
                }
                writer.writerow(row)

        print(f"  Exported {len(checkpoints)} checkpoints to {checkpoints_csv}")

        # Export LoRAs
        loras_csv = output_path / "loras.csv"
        lora_fields = [
            'path', 'name', 'version', 'compatible_architectures', 'family',
            'description', 'tags', 'trigger_words', 'optimal_checkpoints', 'model_metadata'
        ]

        print(f"\nExporting LoRAs...")
        loras = session.query(LoraModel).order_by(LoraModel.name).all()

        # Filter if only_critical_nulls is True
        if only_critical_nulls:
            loras = [l for l in loras if _has_critical_nulls_lora(l)]
            print(f"  Filtering to only records with critical null fields...")

        with open(loras_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=lora_fields)
            writer.writeheader()

            for lora in loras:
                row = {
                    'path': lora.path or '',
                    'name': lora.name or '',
                    'version': lora.version or '',
                    'compatible_architectures': lora.compatible_architectures or '',
                    'family': lora.family or '',
                    'description': lora.description or '',
                    'tags': json.dumps(lora.tags or []),
                    'trigger_words': json.dumps(lora.trigger_words or []),
                    'optimal_checkpoints': json.dumps(lora.optimal_checkpoints or []),
                    'model_metadata': json.dumps(lora.model_metadata or {})
                }
                writer.writerow(row)

        print(f"  Exported {len(loras)} LoRAs to {loras_csv}")

        print(f"\nExport completed successfully!")
        print(f"\nNext steps:")
        print(f"  1. Edit the CSV files to update model metadata")
        print(f"  2. Run: make sync-models-import-csv")

    except Exception as e:
        print(f"\nError during export: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if session:
            session.close()


def import_models_from_csv(input_dir: Optional[str] = None, environment: Optional[str] = None) -> None:
    """Import model metadata from CSV files.

    Reads CSV files (checkpoints.csv and loras.csv) and updates the database
    with the metadata from the files. Matches records by 'name' field.

    Args:
        input_dir: Directory containing CSV files (defaults to io/output/)
        environment: Database environment (dev, demo, test). Defaults to demo.

    For records that don't exist in the database, prompts the user to
    optionally import them as new records (not recommended - use sync-models-from-fs instead).
    """
    from genonaut.db.schema import CheckpointModel, LoraModel

    env = environment or "demo"
    session = None

    try:
        # Determine input directory
        if input_dir is None:
            # Go up from genonaut/db/utils/utils.py to project root
            project_root = Path(__file__).parent.parent.parent.parent
            input_path = project_root / "io" / "output"
        else:
            input_path = Path(input_dir)

        if not input_path.exists():
            print(f"Error: Input directory does not exist: {input_path}")
            sys.exit(1)

        print(f"Importing model metadata from: {input_path}")

        # Get database session
        session = get_database_session(env)

        # Track statistics
        stats = {
            'checkpoints': {'updated': 0, 'unmatched': [], 'errors': 0},
            'loras': {'updated': 0, 'unmatched': [], 'errors': 0}
        }

        # Import checkpoints
        checkpoints_csv = input_path / "checkpoints.csv"
        if checkpoints_csv.exists():
            print(f"\nImporting checkpoints from {checkpoints_csv}...")
            stats['checkpoints'] = _import_model_csv(
                session=session,
                csv_path=checkpoints_csv,
                model_class=CheckpointModel,
                model_type="checkpoint"
            )
        else:
            print(f"Warning: {checkpoints_csv} not found, skipping checkpoints import")

        # Import LoRAs
        loras_csv = input_path / "loras.csv"
        if loras_csv.exists():
            print(f"\nImporting LoRAs from {loras_csv}...")
            stats['loras'] = _import_model_csv(
                session=session,
                csv_path=loras_csv,
                model_class=LoraModel,
                model_type="lora"
            )
        else:
            print(f"Warning: {loras_csv} not found, skipping LoRAs import")

        # Commit all changes
        session.commit()

        # Print summary
        print("\n" + "=" * 80)
        print("IMPORT SUMMARY")
        print("=" * 80)
        print(f"\nCheckpoints:")
        print(f"  Updated: {stats['checkpoints']['updated']}")
        print(f"  Unmatched: {len(stats['checkpoints']['unmatched'])}")
        print(f"  Errors: {stats['checkpoints']['errors']}")

        print(f"\nLoRAs:")
        print(f"  Updated: {stats['loras']['updated']}")
        print(f"  Unmatched: {len(stats['loras']['unmatched'])}")
        print(f"  Errors: {stats['loras']['errors']}")

        # Handle unmatched records
        all_unmatched = stats['checkpoints']['unmatched'] + stats['loras']['unmatched']
        if all_unmatched:
            print(f"\n\nUnmatched records ({len(all_unmatched)} total):")
            for name in sorted(all_unmatched):
                print(f"  {name}")

            print("\n" + "-" * 80)
            print("WARNING: Importing new model records via CSV is NOT recommended!")
            print("Recommended practice: First sync with filesystem using 'make sync-models-from-fs'")
            print("-" * 80)

            # Prompt user to import new records
            response = input("\nDo you want to import these unmatched records as new models? (yes/no): ")
            if response.lower().strip() == 'yes':
                print("\nImporting new records...")
                # Re-process unmatched records with create flag
                if stats['checkpoints']['unmatched']:
                    _import_unmatched_models(
                        session=session,
                        csv_path=input_path / "checkpoints.csv",
                        model_class=CheckpointModel,
                        unmatched_names=stats['checkpoints']['unmatched'],
                        model_type="checkpoint"
                    )
                if stats['loras']['unmatched']:
                    _import_unmatched_models(
                        session=session,
                        csv_path=input_path / "loras.csv",
                        model_class=LoraModel,
                        unmatched_names=stats['loras']['unmatched'],
                        model_type="lora"
                    )
                session.commit()
                print(f"Imported {len(all_unmatched)} new records")
            else:
                print("Skipping import of unmatched records")

        print("\nImport completed successfully!")

    except Exception as e:
        if session:
            session.rollback()
        print(f"\nError during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if session:
            session.close()


def _import_model_csv(
    session: Session,
    csv_path: Path,
    model_class: type,
    model_type: str
) -> Dict[str, any]:
    """Import a single model type CSV file.

    Args:
        session: Database session
        csv_path: Path to CSV file
        model_class: CheckpointModel or LoraModel class
        model_type: "checkpoint" or "lora" for logging

    Returns:
        Dictionary with statistics: updated, unmatched, errors
    """
    stats = {
        'updated': 0,
        'unmatched': [],
        'errors': 0
    }

    # Load all existing records by name
    all_records = session.query(model_class).all()
    records_by_name = {record.name: record for record in all_records if record.name}

    print(f"  Found {len(records_by_name)} existing {model_type} records in database")

    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
            try:
                name = row.get('name', '').strip()

                if not name:
                    print(f"  Warning: Row {row_num} has no name, skipping")
                    stats['errors'] += 1
                    continue

                # Check if record exists
                record = records_by_name.get(name)

                if record is None:
                    # No match found
                    stats['unmatched'].append(name)
                    continue

                # Update record fields
                _update_model_from_csv_row(record, row, model_type)
                stats['updated'] += 1
                print(f"  Updated {name}")

            except Exception as e:
                print(f"  Error processing row {row_num}: {e}")
                stats['errors'] += 1
                continue

    return stats


def _import_unmatched_models(
    session: Session,
    csv_path: Path,
    model_class: type,
    unmatched_names: List[str],
    model_type: str
) -> None:
    """Import unmatched CSV records as new database records.

    Args:
        session: Database session
        csv_path: Path to CSV file
        model_class: CheckpointModel or LoraModel class
        unmatched_names: List of names to import
        model_type: "checkpoint" or "lora" for logging
    """
    unmatched_set = set(unmatched_names)

    # Read CSV again and create new records
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            name = row.get('name', '').strip()

            if name not in unmatched_set:
                continue

            # Create new record
            try:
                new_record = model_class()
                _update_model_from_csv_row(new_record, row, model_type)
                session.add(new_record)
                print(f"  Created new {model_type}: {name}")
            except Exception as e:
                print(f"  Error creating {model_type} '{name}': {e}")


def _parse_array_field(value: str) -> List[str]:
    """Parse an array field value from CSV.

    Supports two formats:
    1. JSON array: ["item1", "item2", "item3"]
    2. Comma-separated: item1, item2, item3

    Args:
        value: Raw field value from CSV

    Returns:
        List of string values
    """
    if not value or not value.strip():
        return []

    value = value.strip()

    # Check if it's already JSON format
    if value.startswith('['):
        try:
            parsed = json.loads(value)
            # Ensure it's a list of strings
            return [str(item) for item in parsed] if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            print(f"    Warning: Invalid JSON array format, parsing as comma-separated")
            # Fall through to comma-separated parsing

    # Parse as comma-separated values
    items = [item.strip() for item in value.split(',')]
    # Filter out empty strings
    return [item for item in items if item]


def _update_model_from_csv_row(record: any, row: Dict[str, str], model_type: str) -> None:
    """Update a model record from a CSV row.

    Args:
        record: CheckpointModel or LoraModel instance
        row: Dictionary of CSV row data
        model_type: "checkpoint" or "lora"
    """
    # Define array fields that should be parsed from comma-separated format
    array_fields = {
        'checkpoint': ['tags'],
        'lora': ['tags', 'trigger_words', 'optimal_checkpoints']
    }

    # Update simple string fields
    for field in ['path', 'name', 'version', 'family', 'description']:
        if field in row:
            value = row[field].strip()
            setattr(record, field, value if value else None)

    # Model-specific fields
    if model_type == "checkpoint":
        if 'architecture' in row:
            value = row['architecture'].strip()
            record.architecture = value if value else None
    else:  # lora
        if 'compatible_architectures' in row:
            value = row['compatible_architectures'].strip()
            record.compatible_architectures = value if value else None

    # Handle array fields with special parsing
    for field in array_fields.get(model_type, []):
        if field in row:
            value = row[field].strip()
            if value:
                parsed_array = _parse_array_field(value)
                setattr(record, field, parsed_array)
            else:
                setattr(record, field, [])

    # Handle model_metadata (non-array JSON field)
    if 'model_metadata' in row and row['model_metadata'].strip():
        try:
            value = json.loads(row['model_metadata'])
            record.model_metadata = value
        except json.JSONDecodeError:
            print(f"    Warning: Invalid JSON for model_metadata, using empty dict")
            record.model_metadata = {}
    else:
        record.model_metadata = {}


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
        "--sync-models-export-csv",
        action="store_true",
        help="Export model metadata to CSV files"
    )

    parser.add_argument(
        "--sync-models-import-csv",
        action="store_true",
        help="Import model metadata from CSV files"
    )

    parser.add_argument(
        "--csv-dir",
        type=str,
        metavar="PATH",
        help="Directory for CSV import/export (defaults to io/output/)"
    )

    parser.add_argument(
        "--only-critical-nulls",
        action="store_true",
        help="Export only models with critical null fields (architecture, metadata, etc.)"
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
    elif args.sync_models_export_csv:
        # Default to demo environment if not specified
        env = args.environment or "demo"
        export_models_to_csv(
            output_dir=args.csv_dir,
            environment=env,
            only_critical_nulls=args.only_critical_nulls
        )
    elif args.sync_models_import_csv:
        # Default to demo environment if not specified
        env = args.environment or "demo"
        import_models_from_csv(input_dir=args.csv_dir, environment=env)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
