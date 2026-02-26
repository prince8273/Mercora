"""Sentiment analysis schemas"""
from typing import List, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SentimentClassification(BaseModel):
    """Sentiment classification result"""
    sentiment: str = Field(..., description="positive, negative, or neutral")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class TopicCluster(BaseModel):
    """Topic cluster from reviews"""
    topic_id: int
    keywords: List[str]
    review_count: int
    sample_reviews: List[str] = Field(default_factory=list, max_length=3)


class FeatureRequest(BaseModel):
    """Extracted feature request"""
    feature: str
    frequency: int
    sample_mentions: List[str] = Field(default_factory=list, max_length=3)


class ComplaintPattern(BaseModel):
    """Identified complaint pattern"""
    pattern: str
    frequency: int
    severity: str = Field(..., description="low, medium, or high")
    sample_reviews: List[str] = Field(default_factory=list, max_length=3)


class SentimentAnalysisResult(BaseModel):
    """Complete sentiment analysis result for a product"""
    product_id: UUID
    aggregate_sentiment: float = Field(..., ge=-1.0, le=1.0, description="Average sentiment score")
    sentiment_distribution: Dict[str, int] = Field(
        ..., 
        description="Count of positive, negative, neutral reviews"
    )
    top_topics: List[TopicCluster] = Field(default_factory=list)
    feature_requests: List[FeatureRequest] = Field(default_factory=list)
    complaint_patterns: List[ComplaintPattern] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    total_reviews: int
    qa_metadata: Optional[Dict] = Field(None, description="Data quality metadata affecting confidence")


class SentimentAnalysisRequest(BaseModel):
    """Request for sentiment analysis"""
    product_ids: List[UUID] = Field(..., min_length=1, description="List of product IDs to analyze")
    num_clusters: Optional[int] = Field(default=5, ge=2, le=10, description="Number of topic clusters")
