"""DB migrations w/ Alembic"""
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

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


# --- Offline mode (generates SQL) ---
def run_migrations_offline() -> None:
    url = get_database_url()
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
    config.set_main_option("sqlalchemy.url", get_database_url())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

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