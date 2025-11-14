"""DB migrations w/ Alembic"""
from __future__ import annotations

import logging
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text
import re

import genonaut.db.schema  # ensure package is imported for migration references

ALEMBIC_ENV_URL_VAR = "ALEMBIC_SQLALCHEMY_URL"

from genonaut.db.schema import Base
from genonaut.db.utils import get_database_url

# Config / logging
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import model
target_metadata = Base.metadata


logger = logging.getLogger("alembic.runtime.migration")


def process_revision_directives(context, revision, directives):
    # Only run when autogenerate is requested
    if getattr(context.config.cmd_opts, "autogenerate", False):
        script = directives[0]
        # In recent Alembic, upgrade_ops has is_empty()
        if hasattr(script, "upgrade_ops") and script.upgrade_ops.is_empty():
            directives[:] = []  # cancel creating the file
            logger.info("No schema changes detected; skipping empty revision. To allow autogenerate to make empty "
                        "revisions, remove 'process_revision_directives=process_revision_directives,' from the "
                        "config.context blocks in the process online/offline funcs in migrate env.py.")


# Optional: tweak autogenerate behavior
def include_object(obj, name, type_, reflected, compare_to):
    """Filter objects during autogenerate to exclude partition-related structures.

    PostgreSQL table partitioning is managed manually via migrations, not via SQLAlchemy models.
    We exclude the partitioned parent table and partition-specific indexes to prevent Alembic
    from trying to drop them during autogenerate.

    Excluded objects:
    - content_items_all: Partitioned parent table (managed manually)
    - content_items_all_uidx_id_src: Partitioned unique index on parent
    - items_uidx_id_src, auto_uidx_id_src: Per-partition unique indexes
    - idx_content_items_created_id_desc, idx_content_items_auto_created_id_desc: Pagination indexes
    - Partition-inherited foreign keys: Auto-generated FKs from partition inheritance
    """
    # Exclude partitioned parent table
    if type_ == "table" and name == "content_items_all":
        return False

    # Exclude partition-related indexes
    partition_indexes = {
        "content_items_all_uidx_id_src",  # Parent partitioned unique index
        "items_uidx_id_src",               # content_items unique index (id, source_type)
        "auto_uidx_id_src",                # content_items_auto unique index (id, source_type)
        "idx_content_items_created_id_desc",      # Keyset pagination index
        "idx_content_items_auto_created_id_desc", # Keyset pagination index
    }
    if type_ == "index" and name in partition_indexes:
        return False

    # Exclude PostgreSQL-specific partial indexes (created via raw SQL, not representable in SQLAlchemy)
    postgres_partial_indexes = {
        "idx_gen_events_error_type",  # Partial index: WHERE error_type IS NOT NULL
        "idx_gen_events_success",     # Partial index: WHERE event_type = 'completion'
    }
    if type_ == "index" and name in postgres_partial_indexes:
        return False

    # Exclude partition-inherited foreign keys on tables that reference content_items_all
    # When we create an FK to content_items_all (partitioned parent), PostgreSQL auto-creates
    # inherited FK constraints from the child partitions (content_items, content_items_auto).
    # These appear in pg_constraint but cannot be dropped directly ("cannot drop inherited constraint").
    # We keep only the explicit FKs we defined (fk_bookmark_content, fk_bookmark_category_cover_content).
    partition_inherited_fks = {
        "bookmarks_content_id_content_source_type_fkey",   # Inherited from content_items partition
        "bookmarks_content_id_content_source_type_fkey1",  # Inherited from content_items_auto partition
        "bookmark_categories_cover_content_id_cover_content_source__fkey",  # Inherited from content_items
        "bookmark_categories_cover_content_id_cover_content_source_fkey1",  # Inherited from content_items_auto
    }
    if type_ == "foreign_key_constraint" and name in partition_inherited_fks:
        return False

    return True


def compare_server_default(context, inspected_column, metadata_column, inspected_default, metadata_default, rendered_metadata_default):
    """Custom comparator for server defaults to handle PostgreSQL::regclass casting differences.

    PostgreSQL stores sequence defaults as nextval('seq_name'::regclass) while SQLAlchemy
    generates nextval('seq_name'). These are functionally identical, so we normalize both
    before comparing to avoid generating unnecessary migrations.

    Returns:
        True: Defaults are different (generate migration)
        False: Defaults are the same (no migration needed)
        None: Use default comparison logic
    """
    # Handle None cases
    if inspected_default is None and metadata_default is None:
        return False
    if inspected_default is None or metadata_default is None:
        return None

    # Convert to strings for comparison
    inspected_str = str(inspected_default).strip()
    metadata_str = str(rendered_metadata_default or metadata_default).strip()

    # Normalize by removing ::regclass from both (in case either has it)
    normalized_inspected = re.sub(r"::regclass\)", ")", inspected_str)
    normalized_metadata = re.sub(r"::regclass\)", ")", metadata_str)

    # Also handle case where one has text() wrapper and other doesn't
    normalized_inspected = re.sub(r"^text\('(.*)'\)$", r"\1", normalized_inspected)
    normalized_metadata = re.sub(r"^text\('(.*)'\)$", r"\1", normalized_metadata)

    # If they match after normalization, consider them equal (no change needed)
    if normalized_inspected == normalized_metadata:
        return False

    # Fall back to default comparison
    return None


# Helper to resolve the database URL. Allows programmatic runners to inject the
# target via alembic.ini while preserving the existing environment behaviour.
def _resolved_database_url() -> str:
    env_url = os.getenv(ALEMBIC_ENV_URL_VAR)
    if env_url and env_url.strip():
        return env_url.strip()

    configured_url = config.get_main_option("sqlalchemy.url")
    if configured_url and configured_url.strip():
        return configured_url.strip()

    return get_database_url()

# --- Offline mode (generates SQL) ---
def run_migrations_offline() -> None:
    url = _resolved_database_url()
    config.set_main_option("sqlalchemy.url", url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,             # detect column type changes
        compare_server_default=compare_server_default,  # custom comparator for server defaults
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


# --- Online mode (applies to the DB) ---
def run_migrations_online() -> None:
    # Inject env URL so alembic.ini can keep sqlalchemy.url blank
    url = _resolved_database_url()
    config.set_main_option("sqlalchemy.url", url)

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
            compare_server_default=compare_server_default,  # custom comparator for server defaults
            render_as_batch=False,  # keep False for Postgres
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
