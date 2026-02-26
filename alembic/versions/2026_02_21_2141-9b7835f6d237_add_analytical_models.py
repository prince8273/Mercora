"""add_analytical_models

Revision ID: 9b7835f6d237
Revises: c1c240aedcfa
Create Date: 2026-02-21 21:41:29.440702

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b7835f6d237'
down_revision: Union[str, None] = 'c1c240aedcfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create analytical_reports table
    op.create_table(
        'analytical_reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('report_type', sa.String(100), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=True),
        sa.Column('key_metrics', sa.JSON(), nullable=True),
        sa.Column('insights', sa.JSON(), nullable=True),
        sa.Column('action_items', sa.JSON(), nullable=True),
        sa.Column('risk_assessment', sa.JSON(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=True),
        sa.Column('period_end', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_analytical_reports_tenant'),
    )
    op.create_index('idx_analytical_reports_tenant', 'analytical_reports', ['tenant_id'])
    op.create_index('idx_analytical_reports_type', 'analytical_reports', ['report_type'])
    op.create_index('idx_analytical_reports_generated', 'analytical_reports', ['generated_at'])
    
    # Create forecast_results table
    op.create_table(
        'forecast_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('forecast_type', sa.String(50), nullable=False),
        sa.Column('predictions', sa.JSON(), nullable=False),
        sa.Column('confidence_intervals', sa.JSON(), nullable=True),
        sa.Column('model_metrics', sa.JSON(), nullable=True),
        sa.Column('seasonality_detected', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('trend_direction', sa.String(20), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('forecast_horizon_days', sa.Integer(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_forecast_results_tenant'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_forecast_results_product'),
    )
    op.create_index('idx_forecast_results_tenant', 'forecast_results', ['tenant_id'])
    op.create_index('idx_forecast_results_product', 'forecast_results', ['product_id'])
    op.create_index('idx_forecast_results_generated', 'forecast_results', ['generated_at'])
    
    # Create aggregated_metrics table
    op.create_table(
        'aggregated_metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=True),
        sa.Column('metric_type', sa.String(100), nullable=False),
        sa.Column('aggregation_period', sa.String(20), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_aggregated_metrics_tenant'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_aggregated_metrics_product'),
        sa.UniqueConstraint('tenant_id', 'product_id', 'metric_type', 'aggregation_period', 'period_start', 
                          name='uq_aggregated_metrics_unique'),
    )
    op.create_index('idx_aggregated_metrics_tenant', 'aggregated_metrics', ['tenant_id'])
    op.create_index('idx_aggregated_metrics_product', 'aggregated_metrics', ['product_id'])
    op.create_index('idx_aggregated_metrics_period', 'aggregated_metrics', ['period_start', 'period_end'])
    op.create_index('idx_aggregated_metrics_type', 'aggregated_metrics', ['metric_type'])


def downgrade() -> None:
    op.drop_table('aggregated_metrics')
    op.drop_table('forecast_results')
    op.drop_table('analytical_reports')
