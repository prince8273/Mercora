"""Sentiment analysis API endpoints"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.review import Review
from src.models.user import User
from src.schemas.sentiment import SentimentAnalysisRequest, SentimentAnalysisResult
from src.schemas.review import ReviewResponse
from src.agents.sentiment_analysis_v2 import EnhancedSentimentAgent
from src.agents.data_qa_agent import DataQAAgent
from src.auth.dependencies import get_current_active_user, get_tenant_id

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/product/{product_id}", response_model=SentimentAnalysisResult)
async def get_product_sentiment(
    product_id: UUID,
    num_clusters: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> SentimentAnalysisResult:
    """
    Get sentiment analysis for a single product (TENANT-ISOLATED).
    
    This endpoint analyzes customer reviews for a specific product and returns:
    - Aggregate sentiment score
    - Sentiment distribution (positive/negative/neutral)
    - Topic clusters from reviews
    - Extracted feature requests
    - Identified complaint patterns
    - QA-adjusted confidence scores
    
    Args:
        product_id: Product UUID
        num_clusters: Number of topic clusters to generate (2-10, default: 5)
        db: Database session
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
        
    Returns:
        Sentiment analysis result with topics, features, and complaints
        
    Example:
        GET /api/v1/sentiment/product/{product_id}?num_clusters=5
    """
    # Validate num_clusters
    if not (2 <= num_clusters <= 10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="num_clusters must be between 2 and 10"
        )
    
    # Initialize agents (TENANT-AWARE)
    sentiment_agent = EnhancedSentimentAgent(tenant_id=tenant_id)
    qa_agent = DataQAAgent(tenant_id=tenant_id)
    
    # Fetch reviews for this product (TENANT-FILTERED)
    result = await db.execute(
        select(Review).where(
            Review.product_id == product_id,
            Review.tenant_id == tenant_id  # TENANT ISOLATION
        )
    )
    review_records = result.scalars().all()
    
    if not review_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No reviews found for product {product_id}"
        )
    
    # Convert to ReviewResponse objects
    reviews = [
        ReviewResponse(
            id=r.id,
            product_id=r.product_id,
            rating=r.rating,
            text=r.text,
            sentiment=r.sentiment,
            sentiment_confidence=r.sentiment_confidence,
            is_spam=r.is_spam,
            created_at=r.created_at,
            source=r.source
        )
        for r in review_records
    ]
    
    # Layer 0: Assess review data quality
    qa_report = qa_agent.assess_review_data_quality(reviews)
    
    # Perform sentiment analysis with QA integration
    analysis_result = sentiment_agent.calculate_aggregate_sentiment_with_qa(
        reviews,
        qa_report
    )
    
    return analysis_result


@router.post("/analyze", response_model=List[SentimentAnalysisResult])
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Analyze sentiment for one or more products (TENANT-ISOLATED).
    
    Args:
        request: Analysis request with product IDs
        db: Database session
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
        
    Returns:
        List of sentiment analysis results
    """
    # Initialize agents (TENANT-AWARE)
    sentiment_agent = EnhancedSentimentAgent(tenant_id=tenant_id)
    qa_agent = DataQAAgent(tenant_id=tenant_id)
    
    results = []
    
    for product_id in request.product_ids:
        # Fetch reviews for this product (TENANT-FILTERED)
        result = await db.execute(
            select(Review).where(
                Review.product_id == product_id,
                Review.tenant_id == tenant_id  # TENANT ISOLATION
            )
        )
        review_records = result.scalars().all()
        
        if not review_records:
            raise HTTPException(
                status_code=404,
                detail=f"No reviews found for product {product_id}"
            )
        
        # Convert to ReviewResponse objects
        reviews = [
            ReviewResponse(
                id=r.id,
                product_id=r.product_id,
                rating=r.rating,
                text=r.text,
                sentiment=r.sentiment,
                sentiment_confidence=r.sentiment_confidence,
                is_spam=r.is_spam,
                created_at=r.created_at,
                source=r.source
            )
            for r in review_records
        ]
        
        # Layer 0: Assess review data quality
        qa_report = qa_agent.assess_review_data_quality(reviews)
        
        # Perform sentiment analysis with QA integration
        analysis_result = sentiment_agent.calculate_aggregate_sentiment_with_qa(
            reviews,
            qa_report
        )
        results.append(analysis_result)
    
    return results
