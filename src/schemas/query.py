"""Query execution schemas"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from src.schemas.pricing import PricingAnalysisResponse
from src.schemas.sentiment import SentimentAnalysisResult
from src.schemas.data_quality import DataQualityReport


class QueryRequest(BaseModel):
    """Request for query execution"""
    query_text: str = Field(..., min_length=1, description="Natural language query")
    product_ids: Optional[List[UUID]] = Field(None, description="Optional list of product IDs to analyze")
    analysis_type: str = Field(default="all", description="Type of analysis: 'pricing', 'sentiment', or 'all'")
    
    model_config = ConfigDict(from_attributes=True)


class StructuredReport(BaseModel):
    """Structured report response from query execution"""
    query_id: UUID
    executive_summary: str
    key_metrics: Dict[str, Any]
    pricing_analysis: Optional[PricingAnalysisResponse] = None
    sentiment_analysis: Optional[List[SentimentAnalysisResult]] = None
    data_quality_report: Optional[DataQualityReport] = Field(None, description="Data quality assessment from QA Agent")
    confidence_score: float = Field(..., ge=0, le=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(from_attributes=True)
