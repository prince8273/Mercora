"""PriceHistory model for tracking price changes"""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.product import GUID


class PriceHistory(Base):
    """Price history model for tracking price changes over time"""
    __tablename__ = "price_history"
    
    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)
    
    # Foreign key to tenant (MULTI-TENANCY)
    tenant_id = Column(GUID(), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Foreign key to product
    product_id = Column(GUID(), ForeignKey('products.id'), nullable=False)
    
    # Price data
    price = Column(Numeric(10, 2), nullable=False)
    
    # Optional competitor reference
    competitor_id = Column(GUID(), ForeignKey('products.id'), nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Source
    source = Column(String(100), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="price_history")
    product = relationship("Product", foreign_keys=[product_id], backref="price_history")
    competitor = relationship("Product", foreign_keys=[competitor_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_price_history_tenant', 'tenant_id'),
        Index('idx_price_history_product_timestamp', 'product_id', 'timestamp'),
        Index('idx_price_history_tenant_timestamp', 'tenant_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<PriceHistory(id={self.id}, product_id={self.product_id}, price={self.price})>"
