"""DB migrations w/ Alembic"""
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text

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


# Optional: tweak autogenerate behavior
def include_object(obj, name, type_, reflected, compare_to):
    # Example: skip alembic's own version table or materialized views, etc.
    # if type_ == "table" and name == "alembic_version":
    #     return False
    return True


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
        compare_server_default=True,   # detect server default changes
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
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
            compare_server_default=True,
            render_as_batch=False,  # keep False for Postgres
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
