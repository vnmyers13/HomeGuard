"""initial_schema

Revision ID: c191a8c36f6a
Revises: 
Create Date: 2026-05-03 01:30:43.560815

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c191a8c36f6a'
down_revision: Union[str, None] = None
branch_labels: Union[tuple, str, None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass