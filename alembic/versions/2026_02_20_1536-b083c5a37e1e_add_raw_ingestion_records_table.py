"""add_raw_ingestion_records_table

Revision ID: b083c5a37e1e
Revises: 001
Create Date: 2026-02-20 15:36:52.012248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b083c5a37e1e'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create raw_ingestion_records table with unique constraint
    op.create_table(
        'raw_ingestion_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('source_id', sa.String(255), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='raw'),
        sa.Column('ingestion_metadata', sa.JSON(), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.String(10), nullable=False, server_default='0'),
        sa.UniqueConstraint('tenant_id', 'source', 'source_id', name='uq_raw_ingestion_tenant_source_id'),
    )
    
    # Create indexes
    op.create_index(
        'idx_raw_ingestion_tenant_source',
        'raw_ingestion_records',
        ['tenant_id', 'source']
    )
    op.create_index(
        'idx_raw_ingestion_retrieved_at',
        'raw_ingestion_records',
        ['retrieved_at']
    )
    op.create_index(
        'idx_raw_ingestion_status',
        'raw_ingestion_records',
        ['status']
    )


def downgrade() -> None:
    op.drop_table('raw_ingestion_records')
