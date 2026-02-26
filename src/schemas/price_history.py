"""PriceHistory schemas"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class PriceHistoryBase(BaseModel):
    """Base price history schema"""
    product_id: UUID
    price: Decimal = Field(..., ge=0, description="Price at this point in time")
    source: str = Field(..., description="Source of the price data")
    competitor_id: Optional[UUID] = Field(None, description="Competitor product ID if applicable")


class PriceHistoryCreate(PriceHistoryBase):
    """Schema for creating a price history record"""
    timestamp: Optional[datetime] = None  # Defaults to now if not provided


class PriceHistoryResponse(PriceHistoryBase):
    """Schema for price history response"""
    id: UUID
    tenant_id: UUID
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PriceChange(BaseModel):
    """Schema for price change detection"""
    product_id: UUID
    old_price: Decimal
    new_price: Decimal
    price_change: Decimal
    price_change_percent: float
    timestamp: datetime
    is_significant: bool = Field(..., description="Whether change exceeds threshold (>5%)")


class PriceTrend(BaseModel):
    """Schema for price trend analysis"""
    product_id: UUID
    current_price: Decimal
    average_price: Decimal
    min_price: Decimal
    max_price: Decimal
    price_volatility: float
    trend_direction: str = Field(..., description="up, down, or stable")
    data_points: int
