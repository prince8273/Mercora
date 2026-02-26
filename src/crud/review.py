"""CRUD operations for Review model"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.review import Review
from src.schemas.review import ReviewCreate
from src.cache.event_bus import get_event_publisher, DataEvent, EventType


async def create_review(
    db: AsyncSession,
    review_data: ReviewCreate,
    tenant_id: UUID
) -> Review:
    """Create a new review for a specific tenant"""
    review = Review(
        tenant_id=tenant_id,  # TENANT ISOLATION
        product_id=review_data.product_id,
        rating=review_data.rating,
        text=review_data.text,
        source=review_data.source,
        sentiment=None,  # Will be populated by sentiment agent
        sentiment_confidence=None,
        is_spam=False  # Will be checked by spam filter
    )
    
    db.add(review)
    await db.flush()
    await db.refresh(review)
    
    # Publish event for cache invalidation
    try:
        publisher = get_event_publisher()
        event = DataEvent(
            event_type=EventType.REVIEW_CREATED,
            tenant_id=tenant_id,
            entity_type='review',
            entity_id=str(review.id)
        )
        await publisher.publish(event)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to publish review created event: {e}")
    
    return review


async def get_review(
    db: AsyncSession,
    review_id: UUID,
    tenant_id: UUID
) -> Optional[Review]:
    """Get a review by ID (tenant-filtered)"""
    result = await db.execute(
        select(Review).where(
            Review.id == review_id,
            Review.tenant_id == tenant_id  # TENANT ISOLATION
        )
    )
    return result.scalar_one_or_none()


async def get_reviews_by_product(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Review]:
    """Get reviews for a specific product (tenant-filtered)"""
    result = await db.execute(
        select(Review)
        .where(
            Review.product_id == product_id,
            Review.tenant_id == tenant_id  # TENANT ISOLATION
        )
        .offset(skip)
        .limit(limit)
        .order_by(Review.created_at.desc())
    )
    return list(result.scalars().all())


async def get_reviews(
    db: AsyncSession,
    tenant_id: UUID,
    skip: int = 0,
    limit: int = 100,
    sentiment: Optional[str] = None,
    exclude_spam: bool = True
) -> List[Review]:
    """Get reviews with optional filtering (tenant-filtered)"""
    query = select(Review).where(Review.tenant_id == tenant_id)  # TENANT ISOLATION
    
    if sentiment:
        query = query.where(Review.sentiment == sentiment)
    
    if exclude_spam:
        query = query.where(Review.is_spam == False)
    
    query = query.offset(skip).limit(limit).order_by(Review.created_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_review_sentiment(
    db: AsyncSession,
    review_id: UUID,
    sentiment: str,
    confidence: float,
    tenant_id: UUID
) -> Optional[Review]:
    """Update sentiment analysis results for a review (tenant-filtered)"""
    review = await get_review(db, review_id, tenant_id)
    if not review:
        return None
    
    review.sentiment = sentiment
    review.sentiment_confidence = confidence
    
    await db.flush()
    await db.refresh(review)
    
    return review


async def mark_review_as_spam(
    db: AsyncSession,
    review_id: UUID,
    tenant_id: UUID,
    is_spam: bool = True
) -> Optional[Review]:
    """Mark a review as spam or not spam (tenant-filtered)"""
    review = await get_review(db, review_id, tenant_id)
    if not review:
        return None
    
    review.is_spam = is_spam
    
    await db.flush()
    await db.refresh(review)
    
    return review


async def delete_review(
    db: AsyncSession,
    review_id: UUID,
    tenant_id: UUID
) -> bool:
    """Delete a review by ID (tenant-filtered)"""
    review = await get_review(db, review_id, tenant_id)
    if not review:
        return False
    
    await db.delete(review)
    await db.flush()
    
    return True


async def get_review_statistics(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID
) -> dict:
    """Get review statistics for a product (tenant-filtered)"""
    from sqlalchemy import func
    
    # Get all reviews for the product
    reviews = await get_reviews_by_product(db, product_id, tenant_id, skip=0, limit=10000)
    
    if not reviews:
        return {
            "total_reviews": 0,
            "average_rating": 0.0,
            "sentiment_distribution": {},
            "spam_count": 0
        }
    
    # Calculate statistics
    total_reviews = len(reviews)
    average_rating = sum(r.rating for r in reviews) / total_reviews
    
    sentiment_distribution = {}
    spam_count = 0
    
    for review in reviews:
        if review.is_spam:
            spam_count += 1
        
        if review.sentiment:
            sentiment_distribution[review.sentiment] = sentiment_distribution.get(review.sentiment, 0) + 1
    
    return {
        "total_reviews": total_reviews,
        "average_rating": round(average_rating, 2),
        "sentiment_distribution": sentiment_distribution,
        "spam_count": spam_count
    }
