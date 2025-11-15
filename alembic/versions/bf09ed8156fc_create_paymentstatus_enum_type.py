"""Create paymentstatus enum type

Revision ID: bf09ed8156fc
Revises: b96c4a6ef5b9
Create Date: 2025-11-14 22:34:04.974997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf09ed8156fc'
down_revision: Union[str, Sequence[str], None] = 'b96c4a6ef5b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE TYPE paymentstatus AS ENUM ('PENDING', 'SUCCESS', 'FAILED')")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TYPE paymentstatus")
