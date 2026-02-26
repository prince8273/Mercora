"""Review schemas"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ReviewBase(BaseModel):
    """Base review schema"""
    product_id: UUID
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    text: str = Field(..., min_length=1, description="Review text")
    source: str = Field(..., description="Source of the review")


class ReviewCreate(ReviewBase):
    """Schema for creating a review"""
    pass


class ReviewResponse(ReviewBase):
    """Schema for review response"""
    id: UUID
    sentiment: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    is_spam: bool = False
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
