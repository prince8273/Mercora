"""Tenant model for multi-tenancy"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Index
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.product import GUID


class Tenant(Base):
    """Tenant model for multi-tenancy support"""
    __tablename__ = "tenants"
    
    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)
    
    # Tenant information
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # Contact information
    contact_email = Column(String(255), nullable=True)
    
    # Subscription & limits
    plan = Column(String(50), default="free", nullable=False)  # free, basic, pro, enterprise
    max_products = Column(Integer, default=100, nullable=False)
    max_users = Column(Integer, default=5, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    roles = relationship("Role", back_populates="tenant")
    products = relationship("Product", back_populates="tenant")
    reviews = relationship("Review", back_populates="tenant")
    sales_records = relationship("SalesRecord", back_populates="tenant")
    price_history = relationship("PriceHistory", back_populates="tenant")
    analytical_reports = relationship("AnalyticalReport", back_populates="tenant")
    forecast_results = relationship("ForecastResult", back_populates="tenant")
    aggregated_metrics = relationship("AggregatedMetrics", back_populates="tenant")
    
    # Indexes
    __table_args__ = (
        Index('idx_tenants_slug', 'slug'),
        Index('idx_tenants_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, slug={self.slug})>"
