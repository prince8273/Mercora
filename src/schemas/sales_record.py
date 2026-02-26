"""SalesRecord schemas"""
from datetime import date as date_type, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SalesRecordBase(BaseModel):
    """Base sales record schema"""
    product_id: UUID
    quantity: int = Field(..., ge=1, description="Quantity sold")
    revenue: Decimal = Field(..., ge=0, description="Revenue generated")
    date: date_type = Field(..., description="Date of sale")
    marketplace: str = Field(..., description="Marketplace where sale occurred")


class SalesRecordCreate(SalesRecordBase):
    """Schema for creating a sales record"""
    metadata: Optional[dict] = None


class SalesRecordUpdate(BaseModel):
    """Schema for updating a sales record"""
    quantity: Optional[int] = Field(None, ge=1)
    revenue: Optional[Decimal] = Field(None, ge=0)
    date: Optional[date_type] = None
    marketplace: Optional[str] = None
    metadata: Optional[dict] = None


class SalesRecordResponse(SalesRecordBase):
    """Schema for sales record response"""
    id: UUID
    tenant_id: UUID
    extra_data: Optional[dict] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SalesAggregation(BaseModel):
    """Schema for aggregated sales data"""
    total_quantity: int
    total_revenue: Decimal
    average_revenue_per_sale: Decimal
    date_range_start: date_type
    date_range_end: date_type
    record_count: int
