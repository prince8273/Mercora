"""add_missing_tables

Revision ID: add_missing_tables_001
Revises: affc34510273
Create Date: 2026-04-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'add_missing_tables_001'
down_revision: Union[str, None] = 'affc34510273'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # competitor_pricing
    op.create_table(
        'competitor_pricing',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('competitor_name', sa.String(255), nullable=True),
        sa.Column('competitor_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('competitor_rating', sa.Float(), nullable=True),
        sa.Column('market_share', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
    )
    op.create_index('idx_competitor_pricing_tenant', 'competitor_pricing', ['tenant_id'])
    op.create_index('idx_competitor_pricing_product', 'competitor_pricing', ['product_id'])

    # promotion_history
    op.create_table(
        'promotion_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('promotion_type', sa.String(100), nullable=True),
        sa.Column('discount_percentage', sa.Float(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
    )
    op.create_index('idx_promotion_history_tenant', 'promotion_history', ['tenant_id'])

    # market_analysis
    op.create_table(
        'market_analysis',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('category', sa.String(255), nullable=True),
        sa.Column('analysis_date', sa.DateTime(), nullable=True),
        sa.Column('market_size', sa.Float(), nullable=True),
        sa.Column('growth_rate', sa.Float(), nullable=True),
        sa.Column('insights', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
    )
    op.create_index('idx_market_analysis_tenant', 'market_analysis', ['tenant_id'])

    # query_history
    op.create_table(
        'query_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('execution_mode', sa.String(50), nullable=True),
        sa.Column('agents_executed', sa.JSON(), nullable=True),
        sa.Column('overall_confidence', sa.Float(), nullable=True),
        sa.Column('execution_time_seconds', sa.Float(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('idx_query_history_tenant_created', 'query_history', ['tenant_id', 'created_at'])
    op.create_index('idx_query_history_user', 'query_history', ['user_id'])


def downgrade() -> None:
    op.drop_table('query_history')
    op.drop_table('market_analysis')
    op.drop_table('promotion_history')
    op.drop_table('competitor_pricing')
