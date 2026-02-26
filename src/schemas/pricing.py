"""Pricing intelligence schemas"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class PriceGap(BaseModel):
    """Price gap between our product and competitor"""
    product_id: UUID
    our_price: Decimal
    competitor_price: Decimal
    gap_amount: Decimal
    gap_percentage: float
    competitor_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class PriceChangeAlert(BaseModel):
    """Alert for significant price changes"""
    product_id: UUID
    old_price: Decimal
    new_price: Decimal
    change_percentage: float
    timestamp: datetime
    competitor_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class Promotion(BaseModel):
    """Promotion details extracted from competitor data"""
    product_id: UUID
    discount_percentage: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class MarginConstraints(BaseModel):
    """Margin constraints for pricing recommendations"""
    min_margin_percentage: float = Field(..., ge=0, le=100)
    max_discount_percentage: float = Field(..., ge=0, le=100)
    
    model_config = ConfigDict(from_attributes=True)


class PricingRecommendation(BaseModel):
    """Dynamic pricing recommendation"""
    product_id: UUID
    current_price: Decimal
    suggested_price: Decimal
    action: str = Field(default="maintain", description="Action: increase, decrease, or maintain")
    reasoning: str
    confidence_score: float = Field(..., ge=0, le=1)
    expected_impact: str
    market_position: str = Field(default="unknown", description="Market position: premium, competitive, or budget")
    qa_metadata: Optional[Dict[str, Any]] = Field(None, description="Data quality metadata affecting confidence")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(from_attributes=True)


class ProductEquivalenceMapping(BaseModel):
    """Mapping between our product and competitor product"""
    our_product_id: UUID
    competitor_product_id: UUID
    confidence: float = Field(..., ge=0, le=1)
    mapping_type: str  # "exact_sku" or "name_similarity"
    
    model_config = ConfigDict(from_attributes=True)


class MarketData(BaseModel):
    """Market data for pricing analysis"""
    competitor_count: int = Field(default=0, ge=0)
    average_competitor_price: Optional[Decimal] = None
    min_competitor_price: Optional[Decimal] = None
    max_competitor_price: Optional[Decimal] = None
    price_trend: Optional[str] = None  # "increasing", "decreasing", "stable"
    
    model_config = ConfigDict(from_attributes=True)


class PricingAnalysisRequest(BaseModel):
    """Request for pricing analysis"""
    product_ids: List[UUID]
    include_recommendations: bool = True
    margin_constraints: Optional[MarginConstraints] = None
    
    model_config = ConfigDict(from_attributes=True)


class PricingAnalysisResponse(BaseModel):
    """Response from pricing analysis"""
    price_gaps: List[PriceGap]
    price_changes: List[PriceChangeAlert]
    promotions: List[Promotion]
    recommendations: List[PricingRecommendation]
    
    model_config = ConfigDict(from_attributes=True)
