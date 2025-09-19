"""add full text search indexes

Revision ID: 27154362fa82
Revises: 5cb2271fa220
Create Date: 2025-09-18 22:58:36.617571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


FULL_TEXT_CONFIG = "english"


def _is_postgresql() -> bool:
    """Return True when the current migration runs against PostgreSQL."""

    bind = op.get_bind()
    return bind.dialect.name == "postgresql"


def _create_full_text_index(table: str, column: str, index_name: str) -> None:
    """Create a GIN index backed by a ``to_tsvector`` expression for the given column."""

    op.execute(
        sa.text(
            f"CREATE INDEX IF NOT EXISTS {index_name} "
            f"ON {table} USING GIN (to_tsvector('{FULL_TEXT_CONFIG}', {column}));"
        )
    )


def _drop_index(index_name: str) -> None:
    """Drop the specified index when it exists."""

    op.execute(sa.text(f"DROP INDEX IF EXISTS {index_name};"))


# revision identifiers, used by Alembic.
revision: str = '27154362fa82'
down_revision: Union[str, Sequence[str], None] = '5cb2271fa220'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    if not _is_postgresql():
        return

    _create_full_text_index(
        table="generation_jobs",
        column="prompt",
        index_name="ix_generation_jobs_prompt_fts",
    )
    _create_full_text_index(
        table="content_items",
        column="title",
        index_name="ix_content_items_title_fts",
    )


def downgrade() -> None:
    """Downgrade schema."""
    if not _is_postgresql():
        return

    _drop_index("ix_content_items_title_fts")
    _drop_index("ix_generation_jobs_prompt_fts")
