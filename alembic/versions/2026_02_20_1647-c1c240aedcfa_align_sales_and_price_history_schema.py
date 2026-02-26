"""align_sales_and_price_history_schema

Revision ID: c1c240aedcfa
Revises: b083c5a37e1e
Create Date: 2026-02-20 16:47:28.053735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1c240aedcfa'
down_revision: Union[str, None] = 'b083c5a37e1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Align sales_records and price_history schema with models.
    
    Changes:
    1. sales_records: Rename columns to match model
       - sale_date -> date
       - unit_price -> (removed, not in model)
       - total_amount -> revenue
       - Add marketplace column
    2. price_history: Rename columns to match model
       - recorded_at -> timestamp
       - Remove currency column (not in model)
       - Add competitor_id column
    """
    
    # Check if we're using SQLite (which doesn't support ALTER COLUMN)
    conn = op.get_bind()
    if conn.dialect.name == 'sqlite':
        # For SQLite, we need to recreate the tables
        
        # 1. Drop old indexes first
        op.drop_index('idx_sales_tenant', 'sales_records')
        op.drop_index('idx_sales_product', 'sales_records')
        op.drop_index('idx_sales_date', 'sales_records')
        op.drop_index('idx_price_history_tenant', 'price_history')
        op.drop_index('idx_price_history_product', 'price_history')
        op.drop_index('idx_price_history_recorded', 'price_history')
        
        # 2. Rename old tables
        op.rename_table('sales_records', 'sales_records_old')
        op.rename_table('price_history', 'price_history_old')
        
        # 3. Create new sales_records table with correct schema
        op.create_table(
            'sales_records',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('tenant_id', sa.String(36), nullable=False),
            sa.Column('product_id', sa.String(36), nullable=False),
            sa.Column('quantity', sa.Integer(), nullable=False),
            sa.Column('revenue', sa.Numeric(10, 2), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('marketplace', sa.String(100), nullable=False),
            sa.Column('extra_data', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_sales_tenant'),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_sales_product'),
        )
        op.create_index('idx_sales_tenant', 'sales_records', ['tenant_id'])
        op.create_index('idx_sales_product_date', 'sales_records', ['product_id', 'date'])
        op.create_index('idx_sales_tenant_date', 'sales_records', ['tenant_id', 'date'])
        
        # 4. Copy data from old table to new table
        op.execute("""
            INSERT INTO sales_records (id, tenant_id, product_id, quantity, revenue, date, marketplace, extra_data, created_at)
            SELECT id, tenant_id, product_id, quantity, total_amount, sale_date, 'default', extra_data, created_at
            FROM sales_records_old
        """)
        
        # 5. Create new price_history table with correct schema
        op.create_table(
            'price_history',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('tenant_id', sa.String(36), nullable=False),
            sa.Column('product_id', sa.String(36), nullable=False),
            sa.Column('price', sa.Numeric(10, 2), nullable=False),
            sa.Column('competitor_id', sa.String(36), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('source', sa.String(100), nullable=False),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_price_history_tenant'),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_price_history_product'),
            sa.ForeignKeyConstraint(['competitor_id'], ['products.id'], name='fk_price_history_competitor'),
        )
        op.create_index('idx_price_history_tenant', 'price_history', ['tenant_id'])
        op.create_index('idx_price_history_product_timestamp', 'price_history', ['product_id', 'timestamp'])
        op.create_index('idx_price_history_tenant_timestamp', 'price_history', ['tenant_id', 'timestamp'])
        
        # 6. Copy data from old table to new table
        op.execute("""
            INSERT INTO price_history (id, tenant_id, product_id, price, competitor_id, timestamp, source)
            SELECT id, tenant_id, product_id, price, NULL, recorded_at, COALESCE(source, 'migration')
            FROM price_history_old
        """)
        
        # 7. Drop old tables
        op.drop_table('sales_records_old')
        op.drop_table('price_history_old')
    
    else:
        # For PostgreSQL, we can use ALTER COLUMN
        # Rename columns in sales_records
        op.alter_column('sales_records', 'sale_date', new_column_name='date')
        op.alter_column('sales_records', 'total_amount', new_column_name='revenue')
        op.drop_column('sales_records', 'unit_price')
        op.add_column('sales_records', sa.Column('marketplace', sa.String(100), nullable=False, server_default='default'))
        
        # Rename columns in price_history
        op.alter_column('price_history', 'recorded_at', new_column_name='timestamp')
        op.drop_column('price_history', 'currency')
        op.add_column('price_history', sa.Column('competitor_id', sa.String(36), nullable=True))
        op.create_foreign_key('fk_price_history_competitor', 'price_history', 'products', ['competitor_id'], ['id'])


def downgrade() -> None:
    """
    Revert schema changes.
    """
    conn = op.get_bind()
    if conn.dialect.name == 'sqlite':
        # For SQLite, recreate old tables
        
        # 1. Rename current tables
        op.rename_table('sales_records', 'sales_records_new')
        op.rename_table('price_history', 'price_history_new')
        
        # 2. Recreate old sales_records table
        op.create_table(
            'sales_records',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('tenant_id', sa.String(36), nullable=False),
            sa.Column('product_id', sa.String(36), nullable=False),
            sa.Column('quantity', sa.Integer(), nullable=False),
            sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
            sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
            sa.Column('sale_date', sa.Date(), nullable=False),
            sa.Column('extra_data', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_sales_tenant'),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_sales_product'),
        )
        
        # 3. Copy data back
        op.execute("""
            INSERT INTO sales_records (id, tenant_id, product_id, quantity, unit_price, total_amount, sale_date, extra_data, created_at)
            SELECT id, tenant_id, product_id, quantity, 0, revenue, date, extra_data, created_at
            FROM sales_records_new
        """)
        
        # 4. Recreate old price_history table
        op.create_table(
            'price_history',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('tenant_id', sa.String(36), nullable=False),
            sa.Column('product_id', sa.String(36), nullable=False),
            sa.Column('price', sa.Numeric(10, 2), nullable=False),
            sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
            sa.Column('recorded_at', sa.DateTime(), nullable=False),
            sa.Column('source', sa.String(50), nullable=True),
            sa.Column('extra_data', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_price_history_tenant'),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_price_history_product'),
        )
        
        # 5. Copy data back
        op.execute("""
            INSERT INTO price_history (id, tenant_id, product_id, price, currency, recorded_at, source, extra_data)
            SELECT id, tenant_id, product_id, price, 'USD', timestamp, source, NULL
            FROM price_history_new
        """)
        
        # 6. Drop new tables
        op.drop_table('sales_records_new')
        op.drop_table('price_history_new')
    
    else:
        # For PostgreSQL
        op.drop_constraint('fk_price_history_competitor', 'price_history', type_='foreignkey')
        op.drop_column('price_history', 'competitor_id')
        op.add_column('price_history', sa.Column('currency', sa.String(3), nullable=False, server_default='USD'))
        op.alter_column('price_history', 'timestamp', new_column_name='recorded_at')
        
        op.drop_column('sales_records', 'marketplace')
        op.add_column('sales_records', sa.Column('unit_price', sa.Numeric(10, 2), nullable=False, server_default='0'))
        op.alter_column('sales_records', 'revenue', new_column_name='total_amount')
        op.alter_column('sales_records', 'date', new_column_name='sale_date')
