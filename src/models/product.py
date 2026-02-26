"""Product model"""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import Column, String, Numeric, Integer, DateTime, JSON, Index, TypeDecorator, CHAR, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from src.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid4.__class__):
                return str(value)
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid4.__class__):
                from uuid import UUID
                return UUID(value)
            else:
                return value


class Product(Base):
    """Product model for storing product information"""
    __tablename__ = "products"
    
    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)
    
    # Foreign key to tenant (MULTI-TENANCY)
    tenant_id = Column(GUID(), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Product identifiers
    sku = Column(String(255), nullable=False)
    normalized_sku = Column(String(255), nullable=False, index=True)
    
    # Product details
    name = Column(String, nullable=False)
    category = Column(String(255), nullable=True)
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    cost = Column(Numeric(10, 2), nullable=True)  # Cost of goods sold
    currency = Column(String(3), nullable=False, default="USD")
    
    # Marketplace
    marketplace = Column(String(100), nullable=False)
    
    # Inventory
    inventory_level = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional data
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="products")
    forecast_results = relationship("ForecastResult", back_populates="product")
    aggregated_metrics = relationship("AggregatedMetrics", back_populates="product")
    
    # Indexes
    __table_args__ = (
        Index('idx_products_tenant_sku_marketplace', 'tenant_id', 'sku', 'marketplace', unique=True),
        Index('idx_products_tenant', 'tenant_id'),
        Index('idx_products_marketplace', 'marketplace'),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, sku={self.sku}, name={self.name})>"
