"""SalesRecord model for historical sales data"""
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.product import GUID


class SalesRecord(Base):
    """Sales record model for tracking historical sales"""
    __tablename__ = "sales_records"
    
    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)
    
    # Foreign key to tenant (MULTI-TENANCY)
    tenant_id = Column(GUID(), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Foreign key to product
    product_id = Column(GUID(), ForeignKey('products.id'), nullable=False)
    
    # Sales data
    quantity = Column(Integer, nullable=False)
    revenue = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False)
    marketplace = Column(String(100), nullable=False)
    
    # Additional metadata
    extra_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="sales_records")
    product = relationship("Product", backref="sales_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_sales_tenant', 'tenant_id'),
        Index('idx_sales_product_date', 'product_id', 'date'),
        Index('idx_sales_tenant_date', 'tenant_id', 'date'),
    )
    
    def __repr__(self):
        return f"<SalesRecord(id={self.id}, product_id={self.product_id}, date={self.date})>"
