"""drop_recommendation_unique_constraint

Revision ID: 528831014776
Revises: cd63f72bf45b
Create Date: 2025-09-19 20:52:26.840370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '528831014776'
down_revision: Union[str, Sequence[str], None] = 'cd63f72bf45b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('unique_user_content_recommendation', 'recommendations', type_='unique')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_unique_constraint(
        'unique_user_content_recommendation',
        'recommendations',
        ['user_id', 'content_item_id', 'algorithm_version'],
    )
