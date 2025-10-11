"""Static data loader for seed data from CSV files.

This module provides functionality to load static seed data from CSV files
in the seed_data_static/ directory and insert them into the database.
"""

import csv
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from genonaut.db.schema import Base

logger = logging.getLogger(__name__)


class StaticDataLoader:
    """Loads static seed data from CSV files."""

    # Fields that should be parsed as JSON arrays from comma-separated strings
    ARRAY_FIELDS = {
        'tags',
        'trigger_words',
        'optimal_checkpoints',
    }

    # Fields that should be parsed as JSON objects
    JSON_FIELDS = {
        'model_metadata',
    }

    def __init__(self, session: Session, static_data_dir: Path):
        """Initialize the static data loader.

        Args:
            session: SQLAlchemy database session
            static_data_dir: Path to directory containing static CSV files
        """
        self.session = session
        self.static_data_dir = static_data_dir
        self.table_model_map = self._build_table_model_map()

    def _build_table_model_map(self) -> Dict[str, Any]:
        """Construct a dynamic mapping of table names to SQLAlchemy model classes."""
        model_map: Dict[str, Any] = {}
        for mapper in Base.registry.mappers:  # type: ignore[attr-defined]
            model_class = mapper.class_
            table_name = getattr(model_class, '__tablename__', None)
            if table_name:
                model_map[table_name] = model_class
        return model_map

    def load_all_static_data(self):
        """Discover and load all CSV files from static data directory."""
        logger.info("Starting static data loading")
        print("\nLoading static seed data from CSV files...")

        if not self.static_data_dir.exists():
            logger.warning(f"Static data directory does not exist: {self.static_data_dir}")
            return

        # Discover CSV files
        csv_files = list(self.static_data_dir.glob('*.csv'))
        if not csv_files:
            logger.info(f"No CSV files found in {self.static_data_dir}")
            return

        logger.info(f"Found {len(csv_files)} CSV files to process")

        # Process each CSV file
        total_rows = 0
        for csv_file in sorted(csv_files):
            rows_inserted = self._load_csv_file(csv_file)
            total_rows += rows_inserted

        logger.info(f"Static data loading completed: {total_rows} total rows inserted")
        print(f"Static data loaded: {total_rows} total rows inserted")

    def _load_csv_file(self, csv_file: Path) -> int:
        """Load a single CSV file into the database.

        Args:
            csv_file: Path to CSV file

        Returns:
            Number of rows inserted
        """
        # Extract table name from filename (e.g., models_checkpoints.csv -> models_checkpoints)
        table_name = csv_file.stem

        # Get corresponding model class
        model_class = self.table_model_map.get(table_name)
        if not model_class:
            logger.warning(f"No model mapping found for table '{table_name}', skipping {csv_file.name}")
            return 0

        logger.info(f"Loading {csv_file.name} into {table_name} table")
        print(f"  Loading {csv_file.name}...")

        # Read CSV file
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            logger.info(f"No data rows in {csv_file.name}")
            return 0

        # Process and insert rows
        inserted_count = 0
        for row in rows:
            processed_row = self._process_row(row, model_class)
            if processed_row:
                try:
                    instance = model_class(**processed_row)
                    self.session.add(instance)
                    inserted_count += 1
                except Exception as e:
                    logger.error(f"Failed to insert row from {csv_file.name}: {e}")
                    logger.error(f"Row data: {processed_row}")
                    raise

        # Commit all inserts for this file
        self.session.commit()
        logger.info(f"Inserted {inserted_count} rows from {csv_file.name}")

        return inserted_count

    def _process_row(self, row: Dict[str, str], model_class) -> Optional[Dict[str, Any]]:
        """Process a CSV row into a format suitable for database insertion.

        Args:
            row: Raw CSV row as dictionary
            model_class: SQLAlchemy model class

        Returns:
            Processed row data, or None if row should be skipped
        """
        # Skip empty rows (all values are empty strings)
        if all(not value.strip() for value in row.values()):
            return None

        processed = {}
        column_types = {column.name: column.type for column in getattr(model_class, "__table__").columns}

        for field_name, value in row.items():
            if not value.strip():
                if field_name in self.ARRAY_FIELDS:
                    processed[field_name] = []
                elif field_name in self.JSON_FIELDS:
                    processed[field_name] = {}
                continue

            column_type = column_types.get(field_name)
            python_type = None
            if column_type is not None:
                try:
                    python_type = column_type.python_type
                except (AttributeError, NotImplementedError):
                    python_type = None

            if field_name in self.ARRAY_FIELDS:
                processed[field_name] = [item.strip() for item in value.split(',') if item.strip()]
                continue

            if field_name in self.JSON_FIELDS:
                try:
                    processed[field_name] = json.loads(value)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in field '{field_name}': {value}")
                    raise ValueError(f"Invalid JSON in field '{field_name}': {e}")
                continue

            if field_name == 'rating':
                try:
                    processed[field_name] = float(value)
                except ValueError:
                    logger.error(f"Invalid rating value: {value}")
                    raise
                continue

            lower_value = value.lower()
            if lower_value in {'true', 'false'}:
                processed[field_name] = lower_value == 'true'
                continue

            if python_type is uuid.UUID:
                processed[field_name] = uuid.UUID(value)
                continue

            if python_type is int:
                processed[field_name] = int(value)
                continue

            if python_type is float:
                processed[field_name] = float(value)
                continue

            processed[field_name] = value

        # Auto-populate filename from path if missing
        if 'path' in processed and 'filename' not in processed:
            path = processed['path']
            filename = Path(path).name
            processed['filename'] = filename

        # Auto-populate name from filename if missing
        if 'filename' in processed and 'name' not in processed:
            filename = processed['filename']
            # Remove .safetensors extension (or any extension)
            name = Path(filename).stem
            processed['name'] = name

        # Add timestamps
        now = datetime.utcnow()
        processed.setdefault('created_at', now)
        if hasattr(model_class, 'updated_at'):
            processed['updated_at'] = now

        return processed


def seed_static_data(session: Session, project_root: Path):
    """Load static seed data from CSV files.

    This is the main entry point for loading static seed data.

    Args:
        session: SQLAlchemy database session
        project_root: Path to project root directory
    """
    static_data_dir = project_root / "genonaut" / "db" / "demo" / "seed_data_static"
    loader = StaticDataLoader(session, static_data_dir)
    loader.load_all_static_data()
