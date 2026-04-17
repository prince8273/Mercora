"""fix_overall_confidence_precision

Revision ID: fix_confidence_precision_001
Revises: add_error_message_001
Create Date: 2026-04-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'fix_confidence_precision_001'
down_revision: Union[str, None] = 'add_error_message_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'query_history',
        'overall_confidence',
        type_=sa.Numeric(6, 2),
        existing_nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        'query_history',
        'overall_confidence',
        type_=sa.Numeric(5, 4),
        existing_nullable=True
    )
