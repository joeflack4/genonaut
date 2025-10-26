"""Export subsets of demo database tables as TSV fixtures.

This utility walks the SQLAlchemy metadata, determines a safe dependency
order, and copies up to N rows per table (respecting foreign-key
relationships) into ``test/db/input/rdbms_init_from_demo``.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from graphlib import TopologicalSorter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import and_, create_engine, func, or_, select
from sqlalchemy.engine import Engine
from sqlalchemy.engine.row import RowMapping
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.schema import Column, Table

from genonaut.db.schema import Base
from genonaut.db.utils import get_database_url, resolve_database_environment

LOGGER = logging.getLogger(__name__)
DEFAULT_OUTPUT_DIR = Path("test/db/input/rdbms_init_from_demo")
EXCLUDED_TABLES = {"alembic_version", "content_items_all"}


@dataclass
class ExportConfig:
    """Configuration for export limits and paths."""

    output_dir: Path
    default_limit: int
    table_limits: Mapping[str, int]
    include_admin_user: bool
    admin_user_id: Optional[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export demo DB slice as TSV fixtures")
    parser.add_argument(
        "--env-target",
        default="demo",
        help="Database environment to read from (default: demo)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write TSV files (default: test/db/input/rdbms_init_from_demo)",
    )
    parser.add_argument(
        "--default-limit",
        type=int,
        default=100,
        help="Default maximum rows per table",
    )
    parser.add_argument(
        "--table-limit",
        action="append",
        default=[],
        metavar="TABLE=LIMIT",
        help="Override row limit for a specific table (can be passed multiple times)",
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        help="Optional subset of tables to export (defaults to all known tables)",
    )
    parser.add_argument(
        "--verbosity",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--exclude-admin-user",
        action="store_true",
        help="Exclude the admin user and related data from export (default: include admin user)",
    )
    parser.add_argument(
        "--admin-user-id",
        default="121e194b-4caa-4b81-ad4f-86ca3919d5b9",
        help="Admin user ID to export with all dependencies (default: demo_admin user)",
    )
    return parser.parse_args()


def build_table_limits(overrides: Sequence[str]) -> Dict[str, int]:
    limits: Dict[str, int] = {}
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"Invalid table limit '{item}'. Expected format TABLE=LIMIT")
        table_name, value = item.split("=", 1)
        table_name = table_name.strip()
        try:
            limit = int(value)
        except ValueError as exc:  # pragma: no cover - argparse validation
            raise ValueError(f"Invalid limit '{value}' for table {table_name}") from exc
        limits[table_name] = limit
    return limits


def candidate_tables(metadata_tables: Mapping[str, Table], include: Optional[Sequence[str]]) -> List[str]:
    include_set = set(include or []) or None
    if include_set is not None:
        unknown = include_set - set(metadata_tables.keys())
        if unknown:
            raise ValueError(f"Unknown table name(s): {', '.join(sorted(unknown))}")
    tables: List[str] = []
    for name in metadata_tables:
        if name in EXCLUDED_TABLES:
            continue
        if include_set is not None and name not in include_set:
            continue
        tables.append(name)
    return tables


def build_dependency_order(tables: Iterable[str]) -> List[str]:
    sorter = TopologicalSorter()
    meta_tables = Base.metadata.tables
    table_set = set(tables)
    for name in tables:
        table = meta_tables[name]
        deps = {
            elem.column.table.name
            for fk in table.foreign_key_constraints
            for elem in fk.elements
            if elem.column.table.name in table_set
        }
        sorter.add(name, *deps)
    return list(sorter.static_order())


def order_columns(table: Table) -> List:
    cols = list(table.primary_key.columns)
    if cols:
        return cols
    preferred = ["created_at", "updated_at", "id"]
    seen = []
    for name in preferred:
        column = table.columns.get(name)
        if column is not None:
            seen.append(column)
    if seen:
        return seen
    return list(table.columns)


def build_fk_filter(
    table: Table, selected_values: Mapping[str, Mapping[str, Sequence]]
) -> tuple[Optional[Any], bool]:
    expressions = []
    for fk in table.foreign_key_constraints:
        clause_parts = []
        for elem in fk.elements:
            parent_name = elem.column.table.name
            parent_col_name = elem.column.name
            child_col = elem.parent
            parent_column_values = selected_values.get(parent_name, {}).get(parent_col_name, set())
            if not parent_column_values and not child_col.nullable:
                return None, True
            if not parent_column_values and child_col.nullable:
                clause_parts.append(child_col.is_(None))
                continue
            comparator = child_col.in_(parent_column_values)
            if child_col.nullable:
                comparator = or_(child_col.is_(None), comparator)
            clause_parts.append(comparator)
        if clause_parts:
            expressions.append(and_(*clause_parts))
    if not expressions:
        return None, False
    return and_(*expressions), False


def fetch_rows(
    engine: Engine,
    table: Table,
    limit: int,
    selected_values: Mapping[str, Mapping[str, Sequence]],
    skip_fk_filter: bool = False,
) -> List[RowMapping]:
    if limit <= 0:
        return []

    stmt = select(table)

    if not skip_fk_filter:
        filter_expr, unsatisfiable = build_fk_filter(table, selected_values)
        if unsatisfiable:
            LOGGER.debug("%s: parent rows missing; selecting without FK filter", table.name)
        elif filter_expr is not None:
            stmt = stmt.where(filter_expr)

    stmt = stmt.order_by(*order_columns(table)).limit(limit)
    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().all()
    return result


def count_rows(engine: Engine, table: Table) -> int:
    stmt = select(func.count()).select_from(table)
    with engine.connect() as conn:
        return conn.execute(stmt).scalar_one()


def primary_key_columns(table: Table) -> Tuple[Column, ...]:
    pk = tuple(table.primary_key.columns)
    if pk:
        return pk
    return tuple(table.columns)


def row_key(table: Table, row: Mapping[str, Any]) -> Tuple[Any, ...]:
    return tuple(row.get(col.name) for col in primary_key_columns(table))


def build_reverse_fk_graph(metadata_tables: Mapping[str, Table]) -> Dict[str, List[Tuple[str, str, str]]]:
    """Build a graph of reverse foreign key relationships.

    This maps each parent table to all child tables that have foreign keys
    pointing to it, enabling efficient lookup of dependent tables.

    Args:
        metadata_tables: Dictionary of table name to Table objects

    Returns:
        Dict mapping parent_table_name -> List[(child_table, child_column, parent_column)]

    Example:
        {
            'users': [
                ('content_items', 'creator_id', 'id'),
                ('generation_jobs', 'user_id', 'id'),
            ],
            'content_items': [
                ('user_interactions', 'content_item_id', 'id'),
            ]
        }
    """
    reverse_fks: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)

    for table_name, table in metadata_tables.items():
        if table_name in EXCLUDED_TABLES:
            continue

        for fk in table.foreign_key_constraints:
            for elem in fk.elements:
                parent_table = elem.column.table.name
                parent_column = elem.column.name
                child_table = table_name
                child_column = elem.parent.name

                reverse_fks[parent_table].append((child_table, child_column, parent_column))

    return dict(reverse_fks)


def fetch_related_rows_recursive(
    engine: Engine,
    table_name: str,
    key_values: Dict[str, Any],
    reverse_fk_graph: Dict[str, List[Tuple[str, str, str]]],
    metadata_tables: Mapping[str, Table],
    exported_rows: MutableMapping[str, Dict[Tuple[Any, ...], Dict[str, Any]]],
    selected_values: MutableMapping[str, MutableMapping[str, set]],
    visited: set[Tuple[str, Tuple[Any, ...]]],
    max_depth: int = 10,
    current_depth: int = 0,
) -> None:
    """Recursively fetch all rows related to a specific record.

    This function performs a depth-first traversal of foreign key relationships,
    fetching all child records that reference the given record, and recursively
    fetching their children.

    Args:
        engine: SQLAlchemy engine for database connection
        table_name: Current table being processed
        key_values: Primary key values of the record (e.g., {'id': '123...'})
        reverse_fk_graph: Map of parent_table -> [(child_table, child_col, parent_col), ...]
        metadata_tables: Dictionary of table name to Table objects
        exported_rows: Storage for exported data (modified in place)
        selected_values: Column value sets for FK filtering (modified in place)
        visited: Set of (table_name, pk_tuple) to prevent infinite loops
        max_depth: Maximum recursion depth (safety limit)
        current_depth: Current recursion level (for logging and depth limiting)

    Algorithm:
        1. Mark current record as visited to prevent loops
        2. Look up child tables in reverse_fk_graph
        3. For each child table:
           - Build WHERE clause matching parent key values
           - Fetch matching child rows
           - Store new rows in exported_rows
           - Recursively process each new child row (if depth < max_depth)
    """
    if current_depth >= max_depth:
        LOGGER.warning(
            "Maximum recursion depth %d reached at %s %s",
            max_depth,
            table_name,
            key_values,
        )
        return

    # Get primary key for the current record to mark as visited
    table = metadata_tables[table_name]
    pk_names = [col.name for col in primary_key_columns(table)]
    pk_tuple = tuple(key_values.get(pk_name) for pk_name in pk_names)

    visit_key = (table_name, pk_tuple)
    if visit_key in visited:
        return

    visited.add(visit_key)

    # Find all child tables that reference this table
    child_relationships = reverse_fk_graph.get(table_name, [])
    if not child_relationships:
        return

    LOGGER.debug(
        "Recursing into %s (depth=%d): found %d child table(s)",
        table_name,
        current_depth,
        len(set(ct for ct, _, _ in child_relationships)),
    )

    for child_table_name, child_col, parent_col in child_relationships:
        if child_table_name in EXCLUDED_TABLES:
            continue

        child_table = metadata_tables[child_table_name]

        # Build WHERE clause: child_col = parent_col_value
        parent_value = key_values.get(parent_col)
        if parent_value is None:
            continue

        child_column = child_table.columns.get(child_col)
        if child_column is None:
            continue

        # Fetch child rows
        stmt = select(child_table).where(child_column == parent_value)
        with engine.connect() as conn:
            child_rows = conn.execute(stmt).mappings().all()

        if not child_rows:
            continue

        # Store child rows
        dict_rows = [dict(row) for row in child_rows]
        added_rows = store_rows(child_table, dict_rows, exported_rows, selected_values)

        if not added_rows:
            continue

        LOGGER.debug(
            "  %s.%s = %s -> fetched %d new row(s) from %s (depth=%d)",
            child_table_name,
            child_col,
            parent_value,
            len(added_rows),
            table_name,
            current_depth,
        )

        # Ensure parent rows for newly added rows
        ensure_parent_rows(child_table, added_rows, engine, exported_rows, selected_values)

        # Recursively fetch children of these rows
        for child_row in added_rows:
            child_pk_values = {
                col.name: child_row.get(col.name) for col in primary_key_columns(child_table)
            }
            fetch_related_rows_recursive(
                engine=engine,
                table_name=child_table_name,
                key_values=child_pk_values,
                reverse_fk_graph=reverse_fk_graph,
                metadata_tables=metadata_tables,
                exported_rows=exported_rows,
                selected_values=selected_values,
                visited=visited,
                max_depth=max_depth,
                current_depth=current_depth + 1,
            )


def store_rows(
    table: Table,
    rows: Iterable[Mapping[str, Any]],
    exported_rows: MutableMapping[str, Dict[Tuple[Any, ...], Dict[str, Any]]],
    selected_values: MutableMapping[str, MutableMapping[str, set]],
) -> List[Dict[str, Any]]:
    stored: List[Dict[str, Any]] = []
    table_store = exported_rows[table.name]
    column_sets = selected_values[table.name]
    for row in rows:
        key = row_key(table, row)
        if key in table_store:
            continue
        row_dict = dict(row)
        table_store[key] = row_dict
        stored.append(row_dict)
        for column_name, value in row_dict.items():
            if value is None:
                continue
            try:
                column_sets[column_name].add(value)
            except TypeError:
                continue
    return stored


def fetch_parent_rows(
    engine: Engine,
    parent_table: Table,
    key_dicts: Sequence[Dict[str, Any]],
) -> List[RowMapping]:
    if not key_dicts:
        return []
    conditions = []
    for key in key_dicts:
        parts = []
        for column_name, value in key.items():
            column = parent_table.columns.get(column_name)
            if column is None:
                continue
            parts.append(column == value)
        if parts:
            conditions.append(and_(*parts))
    if not conditions:
        return []
    stmt = select(parent_table).where(or_(*conditions))
    with engine.connect() as conn:
        return conn.execute(stmt).mappings().all()


def ensure_parent_rows(
    table: Table,
    new_rows: Sequence[Dict[str, Any]],
    engine: Engine,
    exported_rows: MutableMapping[str, Dict[Tuple[Any, ...], Dict[str, Any]]],
    selected_values: MutableMapping[str, MutableMapping[str, set]],
) -> None:
    for fk in table.foreign_key_constraints:
        parent_table = fk.elements[0].column.table
        if parent_table.name in EXCLUDED_TABLES:
            continue
        key_maps: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
        fk_pairs = [
            (elem.parent.name, elem.column.name)
            for elem in fk.elements
        ]
        parent_pk_names = [col.name for col in primary_key_columns(parent_table)]
        parent_store = exported_rows[parent_table.name]

        for row in new_rows:
            key_values: Dict[str, Any] = {}
            skip = False
            for child_col, parent_col in fk_pairs:
                value = row.get(child_col)
                if value is None:
                    skip = True
                    break
                key_values[parent_col] = value
            if skip or not key_values:
                continue
            parent_key = tuple(key_values.get(col) for col in parent_pk_names)
            if parent_key in parent_store:
                continue
            key_maps[parent_key] = key_values

        if not key_maps:
            continue

        fetched = fetch_parent_rows(engine, parent_table, list(key_maps.values()))
        if not fetched:
            continue
        added = store_rows(parent_table, [dict(row) for row in fetched], exported_rows, selected_values)
        if added:
            ensure_parent_rows(parent_table, added, engine, exported_rows, selected_values)


def seed_admin_user_data(
    engine: Engine,
    admin_user_id: str,
    metadata_tables: Mapping[str, Table],
    exported_rows: MutableMapping[str, Dict[Tuple[Any, ...], Dict[str, Any]]],
    selected_values: MutableMapping[str, MutableMapping[str, set]],
) -> None:
    """Seed the admin user and recursively fetch all related records.

    This function ensures the admin user and all their associated data (content,
    interactions, jobs, etc.) are included in the export, regardless of table
    limits. This is critical for E2E tests that depend on a specific admin user.

    Args:
        engine: SQLAlchemy engine for database connection
        admin_user_id: UUID of the admin user to export
        metadata_tables: Dictionary of table name to Table objects
        exported_rows: Storage for exported data (modified in place)
        selected_values: Column value sets for FK filtering (modified in place)

    Algorithm:
        1. Fetch admin user from users table
        2. Store admin user in exported_rows
        3. Build reverse FK graph to find dependent tables
        4. Recursively fetch all rows related to the admin user
        5. Ensure referential integrity by fetching parent rows
    """
    users_table = metadata_tables['users']

    # Fetch the admin user
    id_column = users_table.columns['id']
    stmt = select(users_table).where(id_column == admin_user_id)

    with engine.connect() as conn:
        admin_user_row = conn.execute(stmt).mappings().first()

    if not admin_user_row:
        LOGGER.warning("Admin user %s not found in source database", admin_user_id)
        return

    # Store the admin user
    admin_user_dict = dict(admin_user_row)
    added_rows = store_rows(users_table, [admin_user_dict], exported_rows, selected_values)

    if not added_rows:
        LOGGER.info("Admin user %s already in export", admin_user_id)
        return

    LOGGER.info("Seeding admin user %s with all dependencies", admin_user_id)

    # Build reverse FK graph for recursive fetching
    reverse_fk_graph = build_reverse_fk_graph(metadata_tables)

    # Recursively fetch all related data
    visited: set[Tuple[str, Tuple[Any, ...]]] = set()
    fetch_related_rows_recursive(
        engine=engine,
        table_name='users',
        key_values={'id': admin_user_id},
        reverse_fk_graph=reverse_fk_graph,
        metadata_tables=metadata_tables,
        exported_rows=exported_rows,
        selected_values=selected_values,
        visited=visited,
        max_depth=10,
        current_depth=0,
    )

    # Count how many rows were added for the admin user
    total_rows = sum(len(rows) for rows in exported_rows.values())
    LOGGER.info("Admin user seeding complete: %d total rows in export", total_rows)


def serialize_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (dict, list, set, tuple)):
        return json.dumps(value if not isinstance(value, set) else list(value), ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def write_tsv(table: Table, rows: List[Mapping], config: ExportConfig) -> None:
    if not rows:
        return
    config.output_dir.mkdir(parents=True, exist_ok=True)
    path = config.output_dir / f"{table.name}.tsv"
    column_names = [col.name for col in table.columns]
    order_names = [col.name for col in order_columns(table)]
    rows_sorted = sorted(
        rows,
        key=lambda row: tuple(row.get(name) for name in order_names),
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(column_names)
        for row in rows_sorted:
            writer.writerow([serialize_value(row.get(col)) for col in column_names])
    LOGGER.info("Wrote %s (%d rows) -> %s", table.name, len(rows_sorted), path)


def export_tables(engine: Engine, table_order: Sequence[str], config: ExportConfig) -> None:
    selected_values: MutableMapping[str, MutableMapping[str, set]] = defaultdict(lambda: defaultdict(set))
    exported_rows: MutableMapping[str, Dict[Tuple[Any, ...], Dict[str, Any]]] = defaultdict(dict)

    # Seed admin user data first if requested
    # This ensures the admin user and all dependencies are always included
    if config.include_admin_user and config.admin_user_id:
        LOGGER.info("Pre-seeding admin user %s with all dependencies", config.admin_user_id)
        seed_admin_user_data(
            engine=engine,
            admin_user_id=config.admin_user_id,
            metadata_tables=Base.metadata.tables,
            exported_rows=exported_rows,
            selected_values=selected_values,
        )

    # Continue with normal table export
    # This will add additional rows up to the configured limits
    for table_name in table_order:
        table = Base.metadata.tables[table_name]
        limit = config.table_limits.get(table_name, config.default_limit)
        try:
            rows = fetch_rows(engine, table, limit, selected_values)
        except SQLAlchemyError as exc:
            LOGGER.error("Failed to export %s: %s", table_name, exc)
            raise

        # If FK filter returned no rows but table has data, retry without filter
        if not rows:
            actual_rows = count_rows(engine, table)
            if actual_rows > 0:
                LOGGER.info(
                    "%s: 0 rows matched FK filter but %d exist; retrying without filter",
                    table_name,
                    actual_rows,
                )
                try:
                    rows = fetch_rows(engine, table, limit, selected_values, skip_fk_filter=True)
                except SQLAlchemyError as exc:
                    LOGGER.error("Failed to export %s without FK filter: %s", table_name, exc)
                    raise
                if not rows:
                    raise RuntimeError(
                        f"Table {table_name}: could not fetch rows even without FK filter"
                    )
            else:
                LOGGER.info("Skipping %s (0 rows to export)", table_name)
                continue

        dict_rows = [dict(row) for row in rows]
        added_rows = store_rows(table, dict_rows, exported_rows, selected_values)
        if added_rows:
            ensure_parent_rows(table, added_rows, engine, exported_rows, selected_values)

    for table_name in table_order:
        table = Base.metadata.tables[table_name]
        table_rows = list(exported_rows.get(table_name, {}).values())
        write_tsv(table, table_rows, config)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.verbosity.upper()), format="%(levelname)s %(message)s")

    table_limits = build_table_limits(args.table_limit)
    config = ExportConfig(
        output_dir=args.output_dir,
        default_limit=args.default_limit,
        table_limits=table_limits,
        include_admin_user=not args.exclude_admin_user,
        admin_user_id=args.admin_user_id if not args.exclude_admin_user else None,
    )

    metadata_tables = Base.metadata.tables
    requested_tables = candidate_tables(metadata_tables, args.tables)
    if not requested_tables:
        raise SystemExit("No tables selected for export")

    order = build_dependency_order(requested_tables)
    LOGGER.info("Export order: %s", ", ".join(order))

    environment = resolve_database_environment(environment=args.env_target)
    database_url = get_database_url(environment=environment)
    engine = create_engine(database_url)

    export_tables(engine, order, config)
    LOGGER.info("Export complete")


if __name__ == "__main__":
    main()
