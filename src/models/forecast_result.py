"""Forecast Result model for storing demand forecasts"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.product import GUID


class ForecastResult(Base):
    """
    Forecast Result model for storing demand forecast outputs
    
    This model stores predictions from the Demand Forecast Agent including:
    - Predicted demand values
    - Confidence intervals
    - Seasonality detection
    - Inventory alerts
    """
    __tablename__ = "forecast_results"
    
    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)
    
    # Foreign keys
    tenant_id = Column(GUID(), ForeignKey('tenants.id'), nullable=False, index=True)
    product_id = Column(GUID(), ForeignKey('products.id'), nullable=False, index=True)
    
    # Forecast parameters
    forecast_horizon_days = Column(Integer, nullable=False)
    model_version = Column(String(50), nullable=False)
    
    # Forecast results
    predicted_demand = Column(JSON, nullable=False)  # List[float]
    confidence_intervals = Column(JSON, nullable=False)  # List[Tuple[float, float]]
    confidence_score = Column(Float, nullable=False)
    
    # Seasonality
    seasonality_detected = Column(Boolean, nullable=False, default=False)
    seasonality_pattern = Column(JSON, nullable=True)  # Optional seasonality details
    
    # Inventory alerts
    inventory_alerts = Column(JSON, nullable=True)  # List[InventoryAlert]
    
    # Metadata
    forecast_metadata = Column(JSON, nullable=True)  # Additional forecast details
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    forecast_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="forecast_results")
    product = relationship("Product", back_populates="forecast_results")
    
    # Indexes
    __table_args__ = (
        Index('idx_forecast_results_tenant', 'tenant_id'),
        Index('idx_forecast_results_product', 'product_id'),
        Index('idx_forecast_results_created', 'created_at'),
        Index('idx_forecast_results_tenant_product', 'tenant_id', 'product_id'),
    )
    
    def __repr__(self):
        return f"<ForecastResult(id={self.id}, product_id={self.product_id}, horizon={self.forecast_horizon_days})>"
