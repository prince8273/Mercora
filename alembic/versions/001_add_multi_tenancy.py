"""Add multi-tenancy support

Revision ID: 001
Revises: 
Create Date: 2026-02-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Add multi-tenancy support to all tables.
    
    This migration:
    1. Creates tenants and users tables
    2. Creates products and reviews tables with tenant_id
    3. Creates sales_records and price_history tables with tenant_id
    4. Adds foreign key constraints
    5. Adds indexes on tenant_id columns
    6. Creates a default tenant and admin user
    """
    
    # Generate default tenant ID for existing data
    default_tenant_id = str(uuid.uuid4())
    default_user_id = str(uuid.uuid4())
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('plan', sa.String(50), nullable=False, default='free'),
        sa.Column('max_products', sa.Integer(), nullable=False, default=100),
        sa.Column('max_users', sa.Integer(), nullable=False, default=5),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
    )
    op.create_index('idx_tenants_slug', 'tenants', ['slug'])
    op.create_index('idx_tenants_active', 'tenants', ['is_active'])
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_users_tenant'),
    )
    op.create_index('idx_users_tenant', 'users', ['tenant_id'])
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Insert default tenant for existing data
    op.execute(f"""
        INSERT INTO tenants (id, name, slug, plan, max_products, max_users, is_active, created_at, updated_at)
        VALUES (
            '{default_tenant_id}',
            'Default Tenant',
            'default',
            'free',
            100,
            5,
            1,
            '{datetime.utcnow().isoformat()}',
            '{datetime.utcnow().isoformat()}'
        )
    """)
    
    # Insert default user for default tenant
    # Password: "changeme" (hashed with bcrypt)
    default_password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVqN8LFVS"
    op.execute(f"""
        INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser, tenant_id, created_at, updated_at)
        VALUES (
            '{default_user_id}',
            'admin@default.com',
            '{default_password_hash}',
            'Default Admin',
            1,
            1,
            '{default_tenant_id}',
            '{datetime.utcnow().isoformat()}',
            '{datetime.utcnow().isoformat()}'
        )
    """)
    
    # Create products table with tenant_id from the start
    op.create_table(
        'products',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('sku', sa.String(255), nullable=False),
        sa.Column('normalized_sku', sa.String(255), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(255), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('marketplace', sa.String(100), nullable=False),
        sa.Column('inventory_level', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_products_tenant'),
    )
    op.create_index('idx_products_tenant', 'products', ['tenant_id'])
    op.create_index('idx_products_normalized_sku', 'products', ['normalized_sku'])
    op.create_index('idx_products_marketplace', 'products', ['marketplace'])
    op.create_index('idx_products_tenant_sku_marketplace', 'products', ['tenant_id', 'sku', 'marketplace'], unique=True)
    
    # Create reviews table with tenant_id from the start
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('sentiment', sa.String(20), nullable=True),
        sa.Column('sentiment_confidence', sa.Float(), nullable=True),
        sa.Column('is_spam', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('source', sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_reviews_tenant'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_reviews_product'),
    )
    op.create_index('idx_reviews_tenant', 'reviews', ['tenant_id'])
    op.create_index('idx_reviews_product', 'reviews', ['product_id'])
    op.create_index('idx_reviews_sentiment', 'reviews', ['sentiment'])
    
    # Create sales_records table
    op.create_table(
        'sales_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('sale_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_sales_product'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_sales_tenant'),
    )
    op.create_index('idx_sales_tenant', 'sales_records', ['tenant_id'])
    op.create_index('idx_sales_product', 'sales_records', ['product_id'])
    op.create_index('idx_sales_date', 'sales_records', ['sale_date'])
    
    # Create price_history table
    op.create_table(
        'price_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('recorded_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_price_history_product'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_price_history_tenant'),
    )
    op.create_index('idx_price_history_tenant', 'price_history', ['tenant_id'])
    op.create_index('idx_price_history_product', 'price_history', ['product_id'])
    op.create_index('idx_price_history_recorded', 'price_history', ['recorded_at'])


def downgrade():
    """
    Remove multi-tenancy support.
    
    WARNING: This will delete all data!
    """
    # Drop indexes
    op.drop_index('idx_price_history_recorded', 'price_history')
    op.drop_index('idx_price_history_product', 'price_history')
    op.drop_index('idx_price_history_tenant', 'price_history')
    op.drop_index('idx_sales_date', 'sales_records')
    op.drop_index('idx_sales_product', 'sales_records')
    op.drop_index('idx_sales_tenant', 'sales_records')
    op.drop_index('idx_reviews_sentiment', 'reviews')
    op.drop_index('idx_reviews_product', 'reviews')
    op.drop_index('idx_reviews_tenant', 'reviews')
    op.drop_index('idx_products_tenant_sku_marketplace', 'products')
    op.drop_index('idx_products_marketplace', 'products')
    op.drop_index('idx_products_normalized_sku', 'products')
    op.drop_index('idx_products_tenant', 'products')
    op.drop_index('idx_users_email', 'users')
    op.drop_index('idx_users_tenant', 'users')
    
    # Drop tables
    op.drop_table('price_history')
    op.drop_table('sales_records')
    op.drop_table('reviews')
    op.drop_table('products')
    op.drop_table('users')
    op.drop_table('tenants')
