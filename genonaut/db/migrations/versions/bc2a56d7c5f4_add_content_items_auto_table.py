"""add content_items_auto table

Revision ID: bc2a56d7c5f4
Revises: cd63f72bf45b
Create Date: 2025-09-20 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import genonaut.db.schema


revision: str = 'bc2a56d7c5f4'
down_revision: Union[str, Sequence[str], None] = '528831014776'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgresql() -> bool:
    """Return True when the current migration runs against PostgreSQL."""

    bind = op.get_bind()
    return bind.dialect.name == "postgresql"


def _create_full_text_index(table: str, column: str, index_name: str) -> None:
    """Create a GIN index backed by a ``to_tsvector`` expression for the given column."""

    op.execute(
        sa.text(
            f"CREATE INDEX IF NOT EXISTS {index_name} "
            f"ON {table} USING GIN ("
            f"to_tsvector('english', coalesce({column}, ''))"
            ");"
        )
    )


def _drop_index(index_name: str) -> None:
    """Drop the specified index when it exists."""

    op.execute(sa.text(f"DROP INDEX IF EXISTS {index_name};"))


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'content_items_auto',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('content_data', sa.Text(), nullable=False),
        sa.Column('item_metadata', genonaut.db.schema.JSONColumn(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('tags', genonaut.db.schema.JSONColumn(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_private', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_content_items_auto_content_type'),
        'content_items_auto',
        ['content_type'],
        unique=False,
    )
    op.create_index(
        op.f('ix_content_items_auto_creator_id'),
        'content_items_auto',
        ['creator_id'],
        unique=False,
    )

    if _is_postgresql():
        _create_full_text_index(
            table='content_items_auto',
            column='title',
            index_name='cia_title_fts_idx',
        )


def downgrade() -> None:
    """Downgrade schema."""
    if _is_postgresql():
        _drop_index('cia_title_fts_idx')

    op.drop_index(op.f('ix_content_items_auto_creator_id'), table_name='content_items_auto')
    op.drop_index(op.f('ix_content_items_auto_content_type'), table_name='content_items_auto')
    op.drop_table('content_items_auto')
