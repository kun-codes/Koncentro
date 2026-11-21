"""add enable_app_blocker to workspaces table

Revision ID: 8341f3fe59da
Revises: 1fe1f4e0eb64
Create Date: 2026-11-21 20:26:26.652316

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8341f3fe59da'
down_revision: Union[str, None] = '1fe1f4e0eb64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default backfills existing workspaces with True, matching the Python-side default of the column
    with op.batch_alter_table('workspaces', schema=None) as batch_op:
        batch_op.add_column(sa.Column('enable_app_blocker', sa.Boolean(), nullable=True, server_default='1'))


def downgrade() -> None:
    with op.batch_alter_table('workspaces', schema=None) as batch_op:
        batch_op.drop_column('enable_app_blocker')
