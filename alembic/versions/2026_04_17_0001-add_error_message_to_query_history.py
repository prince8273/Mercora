"""add_error_message_to_query_history

Revision ID: add_error_message_001
Revises: fix_uuid_types_001
Create Date: 2026-04-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'add_error_message_001'
down_revision: Union[str, None] = 'fix_uuid_types_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'query_history',
        sa.Column('error_message', sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('query_history', 'error_message')
