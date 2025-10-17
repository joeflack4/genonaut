"""Remove idx_user_search_history_user_query index

Revision ID: e804355b2a87
Revises: 20aad43c6683
Create Date: 2025-10-17 11:16:20.011436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e804355b2a87'
down_revision: Union[str, Sequence[str], None] = '20aad43c6683'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the idx_user_search_history_user_query index
    op.drop_index('idx_user_search_history_user_query', table_name='user_search_history')


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate the idx_user_search_history_user_query index
    op.create_index('idx_user_search_history_user_query', 'user_search_history', ['user_id', 'search_query'], unique=False)
