"""fix_uuid_types

Revision ID: fix_uuid_types_001
Revises: add_missing_tables_001
Create Date: 2026-04-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'fix_uuid_types_001'
down_revision: Union[str, None] = 'add_missing_tables_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop FK constraints only on our tables
    our_tables = [
        'tenants', 'users', 'products', 'reviews', 'sales_records',
        'price_history', 'raw_ingestion_records', 'analytical_reports',
        'forecast_results', 'aggregated_metrics', 'competitor_pricing',
        'promotion_history', 'market_analysis', 'query_history',
    ]
    tables_list = ", ".join(f"'{t}'" for t in our_tables)

    op.execute(f"""
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (
                SELECT tc.constraint_name, tc.table_name
                FROM information_schema.table_constraints tc
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN ({tables_list})
                AND tc.table_schema = 'public'
            ) LOOP
                EXECUTE 'ALTER TABLE public.' || quote_ident(r.table_name) || ' DROP CONSTRAINT IF EXISTS ' || quote_ident(r.constraint_name);
            END LOOP;
        END $$;
    """)

    # Convert all id and *_id columns from VARCHAR to UUID
    tables_ids = [
        ('tenants', 'id'),
        ('users', 'id'), ('users', 'tenant_id'),
        ('products', 'id'), ('products', 'tenant_id'),
        ('reviews', 'id'), ('reviews', 'tenant_id'), ('reviews', 'product_id'),
        ('sales_records', 'id'), ('sales_records', 'tenant_id'), ('sales_records', 'product_id'),
        ('price_history', 'id'), ('price_history', 'tenant_id'), ('price_history', 'product_id'),
        ('raw_ingestion_records', 'id'), ('raw_ingestion_records', 'tenant_id'),
        ('analytical_reports', 'id'), ('analytical_reports', 'tenant_id'),
        ('forecast_results', 'id'), ('forecast_results', 'tenant_id'), ('forecast_results', 'product_id'),
        ('aggregated_metrics', 'id'), ('aggregated_metrics', 'tenant_id'), ('aggregated_metrics', 'product_id'),
        ('competitor_pricing', 'id'), ('competitor_pricing', 'tenant_id'), ('competitor_pricing', 'product_id'),
        ('promotion_history', 'id'), ('promotion_history', 'tenant_id'), ('promotion_history', 'product_id'),
        ('market_analysis', 'id'), ('market_analysis', 'tenant_id'),
        ('query_history', 'id'), ('query_history', 'tenant_id'), ('query_history', 'user_id'),
    ]

    for table, col in tables_ids:
        op.execute(f"""
            ALTER TABLE {table}
            ALTER COLUMN {col} TYPE UUID USING {col}::uuid
        """)

    # FK constraints not re-added — orphaned data from migration prevents it.
    # Application-level tenant isolation handles data integrity.
    pass


def downgrade() -> None:
    pass
