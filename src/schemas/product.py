"""Product Pydantic schemas"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_serializer


class ProductBase(BaseModel):
    """Base product schema with common fields"""
    sku: str = Field(..., min_length=1, max_length=255, description="Stock Keeping Unit")
    name: str = Field(..., min_length=1, description="Product name")
    category: Optional[str] = Field(None, max_length=255, description="Product category")
    price: Decimal = Field(..., gt=0, description="Product price")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")
    marketplace: str = Field(..., min_length=1, max_length=100, description="Marketplace identifier")
    inventory_level: Optional[int] = Field(None, ge=0, description="Current inventory level")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata", alias="extra_metadata")


class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product"""
    sku: Optional[str] = Field(None, min_length=1, max_length=255)
    name: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, max_length=255)
    price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    marketplace: Optional[str] = Field(None, min_length=1, max_length=100)
    inventory_level: Optional[int] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class ProductResponse(ProductBase):
    """Schema for product API responses"""
    id: UUID
    normalized_sku: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
