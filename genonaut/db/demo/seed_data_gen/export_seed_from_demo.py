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
    config = ExportConfig(output_dir=args.output_dir, default_limit=args.default_limit, table_limits=table_limits)

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
