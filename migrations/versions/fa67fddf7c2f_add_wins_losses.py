"""add wins/losses

Revision ID: fa67fddf7c2f
Revises: 
Create Date: 2025-09-24 16:59:19.631992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa67fddf7c2f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # adiciona colunas novas na tabela teams
    op.add_column('teams', sa.Column('wins', sa.Integer(), nullable=True))
    op.add_column('teams', sa.Column('losses', sa.Integer(), nullable=True))
    op.add_column('teams', sa.Column('points', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('teams', 'wins')
    op.drop_column('teams', 'losses')
    op.drop_column('teams', 'points')
