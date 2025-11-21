"""Add bedrooms, bathrooms, and area_sqm columns to properties

Revision ID: aa1b2c3d4e5f
Revises: e08b90822536
Create Date: 2025-11-21 16:19:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'aa1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = 'e08b90822536'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add optional bedrooms, bathrooms, area_sqm columns."""
    op.add_column('properties', sa.Column('bedrooms', sa.Integer(), nullable=True))
    op.add_column('properties', sa.Column('bathrooms', sa.Integer(), nullable=True))
    op.add_column('properties', sa.Column('area_sqm', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema by removing bedrooms, bathrooms, area_sqm columns."""
    op.drop_column('properties', 'area_sqm')
    op.drop_column('properties', 'bathrooms')
    op.drop_column('properties', 'bedrooms')
