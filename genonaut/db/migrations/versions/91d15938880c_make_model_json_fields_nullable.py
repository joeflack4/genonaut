"""make model json fields nullable

Revision ID: 91d15938880c
Revises: 4e6bfd99c6ee
Create Date: 2025-10-07 20:01:56.466875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91d15938880c'
down_revision: Union[str, Sequence[str], None] = '4e6bfd99c6ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make JSON columns nullable in models_checkpoints
    op.alter_column('models_checkpoints', 'tags',
                    existing_type=sa.JSON(),
                    nullable=True)
    op.alter_column('models_checkpoints', 'model_metadata',
                    existing_type=sa.JSON(),
                    nullable=True)

    # Make JSON columns nullable in models_loras
    op.alter_column('models_loras', 'tags',
                    existing_type=sa.JSON(),
                    nullable=True)
    op.alter_column('models_loras', 'trigger_words',
                    existing_type=sa.JSON(),
                    nullable=True)
    op.alter_column('models_loras', 'optimal_checkpoints',
                    existing_type=sa.JSON(),
                    nullable=True)
    op.alter_column('models_loras', 'model_metadata',
                    existing_type=sa.JSON(),
                    nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert JSON columns to not nullable in models_loras
    op.alter_column('models_loras', 'model_metadata',
                    existing_type=sa.JSON(),
                    nullable=False)
    op.alter_column('models_loras', 'optimal_checkpoints',
                    existing_type=sa.JSON(),
                    nullable=False)
    op.alter_column('models_loras', 'trigger_words',
                    existing_type=sa.JSON(),
                    nullable=False)
    op.alter_column('models_loras', 'tags',
                    existing_type=sa.JSON(),
                    nullable=False)

    # Revert JSON columns to not nullable in models_checkpoints
    op.alter_column('models_checkpoints', 'model_metadata',
                    existing_type=sa.JSON(),
                    nullable=False)
    op.alter_column('models_checkpoints', 'tags',
                    existing_type=sa.JSON(),
                    nullable=False)
