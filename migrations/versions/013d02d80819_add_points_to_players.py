"""add points to players

Revision ID: 013d02d80819
Revises: fa67fddf7c2f
Create Date: 2025-09-24 17:58:02.690069

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '013d02d80819'
down_revision: Union[str, Sequence[str], None] = 'fa67fddf7c2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.add_column('players', sa.Column('points', sa.Integer(), server_default='0'))

def downgrade():
    op.drop_column('players', 'points')

