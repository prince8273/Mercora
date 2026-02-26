"""Aggregated Metrics model for storing pre-computed analytics"""
from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Date, Float, Integer, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.product import GUID


class AggregatedMetrics(Base):
    """
    Aggregated Metrics model for storing pre-computed analytics
    
    This model stores aggregated metrics for quick retrieval including:
    - Sales metrics (revenue, quantity, growth)
    - Pricing metrics (average price, price trends)
    - Sentiment metrics (average rating, sentiment distribution)
    - Inventory metrics (stock levels, turnover)
    """
    __tablename__ = "aggregated_metrics"
    
    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)
    
    # Foreign keys
    tenant_id = Column(GUID(), ForeignKey('tenants.id'), nullable=False, index=True)
    product_id = Column(GUID(), ForeignKey('products.id'), nullable=True, index=True)  # Null for tenant-level metrics
    
    # Metric identification
    metric_type = Column(String(50), nullable=False, index=True)  # sales, pricing, sentiment, inventory
    metric_name = Column(String(100), nullable=False, index=True)  # total_revenue, avg_price, etc.
    aggregation_period = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly, yearly
    
    # Time period
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    
    # Metric values
    metric_value = Column(Float, nullable=False)
    metric_count = Column(Integer, nullable=True)  # Number of data points
    
    # Trend information
    previous_value = Column(Float, nullable=True)
    change_percentage = Column(Float, nullable=True)
    trend_direction = Column(String(20), nullable=True)  # up, down, stable
    
    # Additional details
    metric_details = Column(JSON, nullable=True)  # Additional metric-specific data
    
    # Metadata
    calculation_method = Column(String(100), nullable=True)
    data_quality_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="aggregated_metrics")
    product = relationship("Product", back_populates="aggregated_metrics")
    
    # Indexes
    __table_args__ = (
        Index('idx_aggregated_metrics_tenant', 'tenant_id'),
        Index('idx_aggregated_metrics_product', 'product_id'),
        Index('idx_aggregated_metrics_type', 'metric_type'),
        Index('idx_aggregated_metrics_name', 'metric_name'),
        Index('idx_aggregated_metrics_period', 'period_start', 'period_end'),
        Index('idx_aggregated_metrics_tenant_type_period', 'tenant_id', 'metric_type', 'period_start'),
    )
    
    def __repr__(self):
        return f"<AggregatedMetrics(id={self.id}, type={self.metric_type}, name={self.metric_name}, value={self.metric_value})>"
