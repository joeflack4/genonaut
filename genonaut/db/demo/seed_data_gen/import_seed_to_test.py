"""Import TSV fixtures into the test database in dependency order."""

from __future__ import annotations

import argparse
import csv
import json
import logging
from datetime import date, datetime, time
from decimal import Decimal
from graphlib import TopologicalSorter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import sqltypes
from sqlalchemy.sql.schema import Column, Table

from genonaut.db.schema import Base, JSONColumn
from genonaut.db.utils import get_database_url, resolve_database_environment

LOGGER = logging.getLogger(__name__)
DEFAULT_INPUT_DIR = Path("test/db/input/rdbms_init_from_demo")
EXCLUDED_TABLES = {"alembic_version", "content_items_all"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import TSV fixtures into test database")
    parser.add_argument(
        "--env-target",
        default="test",
        help="Database environment to write to (default: test)",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory containing TSV fixtures",
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        help="Optional subset of tables to import (derived from filenames when omitted)",
    )
    parser.add_argument(
        "--table",
        action="append",
        dest="table_list",
        help="Import only the specified table (can be passed multiple times)",
    )
    parser.add_argument(
        "--truncate-first",
        action="store_true",
        help="Truncate destination tables before importing",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Compare TSV row counts with database counts after import",
    )
    parser.add_argument(
        "--set-alembic-version",
        action="store_true",
        help="Set alembic_version table after import (default: False)",
    )
    parser.add_argument(
        "--alembic-version",
        default="672c99981361",
        help="Version hash to store in alembic_version when --set-alembic-version is used (default: 672c99981361)",
    )
    parser.add_argument(
        "--verbosity",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging verbosity",
    )
    return parser.parse_args()


def available_tables(input_dir: Path) -> List[str]:
    tables = []
    for path in sorted(input_dir.glob("*.tsv")):
        tables.append(path.stem)
    return tables


def candidate_tables(
    metadata_tables: Mapping[str, Table], names: Optional[Sequence[str]], input_dir: Path
) -> List[str]:
    include = list(names) if names else available_tables(input_dir)
    include_set = set(include)
    unknown = include_set - set(metadata_tables.keys())
    if unknown:
        raise ValueError(f"Unknown table name(s): {', '.join(sorted(unknown))}")
    return [name for name in include if name not in EXCLUDED_TABLES]


def dependency_order(tables: Iterable[str]) -> List[str]:
    sorter = TopologicalSorter()
    meta_tables = Base.metadata.tables
    table_set = set(tables)
    for name in tables:
        deps = {
            elem.column.table.name
            for fk in meta_tables[name].foreign_key_constraints
            for elem in fk.elements
            if elem.column.table.name in table_set
        }
        sorter.add(name, *deps)
    return list(sorter.static_order())


def reverse_dependency_order(tables: Sequence[str]) -> List[str]:
    return list(reversed(tables))


def parse_cell(raw: str, column: Column) -> Any:
    col_type = column.type
    if raw == "":
        if isinstance(col_type, (sqltypes.String, sqltypes.Text)):
            return ""
        return None
    try:
        python_type = col_type.python_type  # type: ignore[attr-defined]
    except (NotImplementedError, AttributeError):
        python_type = None

    if isinstance(col_type, postgresql.UUID):
        return UUID(raw)
    if isinstance(col_type, sqltypes.Boolean):
        return raw.lower() in {"t", "true", "1", "yes"}
    if isinstance(col_type, sqltypes.Integer):
        return int(raw)
    if isinstance(col_type, sqltypes.Float):
        return float(raw)
    if isinstance(col_type, sqltypes.Numeric):
        return Decimal(raw)
    if isinstance(col_type, sqltypes.DateTime):
        return datetime.fromisoformat(raw)
    if isinstance(col_type, sqltypes.Date):
        return date.fromisoformat(raw)
    if isinstance(col_type, sqltypes.Time):
        return time.fromisoformat(raw)
    if isinstance(col_type, (JSONColumn, sqltypes.JSON, postgresql.JSONB)):
        return json.loads(raw)
    if python_type == str or isinstance(col_type, (sqltypes.String, sqltypes.Text)):
        return raw
    if python_type is not None:
        return python_type(raw)
    return raw


def load_rows(path: Path, table: Table) -> List[Dict[str, Any]]:
    if not path.exists():
        LOGGER.info("Skipping %s (missing %s)", table.name, path)
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows: List[Dict[str, Any]] = []
        for raw_row in reader:
            converted: Dict[str, Any] = {}
            for column_name, value in raw_row.items():
                column = table.columns.get(column_name)
                if column is None:
                    continue
                converted[column_name] = parse_cell(value, column)
            rows.append(converted)
    return rows


def truncate_tables(engine: Engine, tables: Sequence[str]) -> None:
    with engine.begin() as conn:
        for name in tables:
            LOGGER.info("Truncating %s", name)
            conn.execute(text(f"TRUNCATE TABLE {name} RESTART IDENTITY CASCADE"))


def insert_rows(engine: Engine, table: Table, rows: List[Mapping[str, Any]]) -> tuple[int, int]:
    """Insert rows into table, returning (inserted_count, skipped_count).

    Uses ON CONFLICT DO NOTHING to skip rows that would violate any unique constraints.
    Also catches and reports foreign key violations.
    """
    if not rows:
        return 0, 0
    stmt = pg_insert(table).values(rows)

    # Use ON CONFLICT DO NOTHING without specifying columns
    # This catches all unique constraint violations (PK + unique columns like tags.name)
    stmt = stmt.on_conflict_do_nothing()

    try:
        with engine.begin() as conn:
            result = conn.execute(stmt)
            inserted = result.rowcount
        skipped = len(rows) - inserted
        return inserted, skipped
    except SQLAlchemyError as e:
        # Handle foreign key violations and other errors
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'ForeignKeyViolation' in error_msg or 'foreign key constraint' in error_msg.lower():
            LOGGER.warning(
                "%s: Skipping all %d rows due to foreign key constraint violations (referenced data may not exist)",
                table.name,
                len(rows),
            )
            return 0, len(rows)
        else:
            # Re-raise other errors
            raise


def import_tables(engine: Engine, order: Sequence[str], input_dir: Path) -> None:
    for name in order:
        table = Base.metadata.tables[name]
        path = input_dir / f"{name}.tsv"
        rows = load_rows(path, table)
        inserted, skipped = insert_rows(engine, table, rows)
        if skipped > 0:
            LOGGER.info(
                "%s: %d new rows inserted, %d skipped (already present)",
                name,
                inserted,
                skipped,
            )
        else:
            LOGGER.info("%s: %d new rows inserted", name, inserted)


def file_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def verify_counts(engine: Engine, tables: Sequence[str], input_dir: Path) -> None:
    with engine.connect() as conn:
        for name in tables:
            path = input_dir / f"{name}.tsv"
            expected = file_row_count(path)
            if expected == 0:
                continue
            db_count = conn.execute(text(f"SELECT COUNT(*) FROM {name}"))
            actual = db_count.scalar_one()
            if actual < expected:
                LOGGER.warning(
                    "Table %s has %d rows in DB but %d rows in fixture", name, actual, expected
                )
            else:
                LOGGER.debug("Verified %s count (%d >= %d)", name, actual, expected)


def ensure_alembic_version(engine: Engine, version: str) -> None:
    statement_create = text(
        "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"
    )
    with engine.begin() as conn:
        conn.execute(statement_create)
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:version)"),
            {"version": version},
        )
    LOGGER.info("Set alembic_version to %s", version)


def reset_sequences(engine: Engine, tables: Sequence[str]) -> None:
    """Reset all IDENTITY sequences to match actual table data.

    When importing data with explicit IDs, PostgreSQL sequences don't automatically
    advance. This function resets each table's sequence to MAX(id) + 1 to prevent
    duplicate key violations on subsequent inserts.

    Only resets sequences for tables with integer primary keys (skips UUID PKs).

    Args:
        engine: SQLAlchemy engine for database connection
        tables: List of table names to reset sequences for
    """
    with engine.begin() as conn:
        for table_name in tables:
            # Skip tables that don't have id columns or sequences
            table = Base.metadata.tables.get(table_name)
            if table is None or not hasattr(table.c, 'id'):
                continue

            # Skip tables with non-integer primary keys (e.g., UUID)
            id_column = table.c.id
            if not isinstance(id_column.type, sqltypes.Integer):
                LOGGER.debug("Skipping %s (non-integer primary key)", table_name)
                continue

            # Use pg_get_serial_sequence to find the sequence name
            # Set to MAX(id) + 1, or 1 if table is empty
            # The 'false' parameter means the value is not immediately used
            conn.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, false);"
            ))
            LOGGER.info("Reset sequence for %s", table_name)


def verify_alembic_version(engine: Engine, should_be_set: bool) -> None:
    """Verify that alembic_version table exists and has a valid value.

    Args:
        engine: SQLAlchemy engine for database connection
        should_be_set: Whether alembic_version should have been set (from --set-alembic-version flag)

    Raises:
        RuntimeError: If alembic_version table doesn't exist or has no value
    """
    with engine.connect() as conn:
        # Check if alembic_version table exists
        table_exists = conn.execute(text(
            "SELECT EXISTS ("
            "SELECT FROM information_schema.tables "
            "WHERE table_name = 'alembic_version'"
            ")"
        )).scalar()

        if not table_exists:
            if should_be_set:
                raise RuntimeError(
                    "ERROR: alembic_version table does not exist after import. "
                    "This should not happen when --set-alembic-version is used."
                )
            else:
                raise RuntimeError(
                    "ERROR: alembic_version table does not exist. "
                    "Please re-run with --set-alembic-version flag to initialize the database schema version."
                )

        # Check if alembic_version has a value
        version_result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = version_result.scalar()

        if not version:
            if should_be_set:
                raise RuntimeError(
                    "ERROR: alembic_version table is empty after import. "
                    "This should not happen when --set-alembic-version is used."
                )
            else:
                raise RuntimeError(
                    "ERROR: alembic_version table is empty. "
                    "Please re-run with --set-alembic-version flag to set the database schema version."
                )

        LOGGER.info("Verified alembic_version: %s", version)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.verbosity.upper()), format="%(levelname)s %(message)s")

    metadata_tables = Base.metadata.tables
    requested_tables: Optional[List[str]] = None
    if args.tables or args.table_list:
        requested_tables = []
        if args.tables:
            requested_tables.extend(args.tables)
        if args.table_list:
            requested_tables.extend(args.table_list)
    target_tables = candidate_tables(metadata_tables, requested_tables, args.input_dir)
    if not target_tables:
        LOGGER.warning("No tables selected for import")
        return

    order = dependency_order(target_tables)
    LOGGER.info("Import order: %s", ", ".join(order))

    environment = resolve_database_environment(environment=args.env_target)
    database_url = get_database_url(environment=environment)
    engine = create_engine(database_url)

    if args.truncate_first:
        truncate_tables(engine, reverse_dependency_order(order))

    if args.set_alembic_version:
        ensure_alembic_version(engine, args.alembic_version)

    import_tables(engine, order, args.input_dir)
    reset_sequences(engine, order)

    if args.verify:
        verify_counts(engine, order, args.input_dir)

    # Verify alembic_version is properly set
    verify_alembic_version(engine, args.set_alembic_version)

    LOGGER.info("Import complete")


if __name__ == "__main__":
    main()
