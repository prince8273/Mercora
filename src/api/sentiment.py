"""Sentiment analysis API endpoints"""
import json
from typing import Dict
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.review import Review
from src.models.user import User
from src.schemas.sentiment import SentimentAnalysisResult, TopicCluster
from src.auth.dependencies import get_current_active_user, get_tenant_id
from src.cache.instance import get_cache_manager


def _normalize_sentiment(val: str | None) -> str:
    if not val:
        return "neutral"
    if val in ("positive", "neutral", "negative"):
        return val
    try:
        score = float(val)
        return "positive" if score >= 0.6 else ("neutral" if score >= 0.4 else "negative")
    except ValueError:
        return "neutral"


def _cutoff(time_range: str) -> datetime | None:
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = days_map.get(time_range)
    return datetime.utcnow() - timedelta(days=days) if days else None


router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/product/{product_id}", response_model=SentimentAnalysisResult)
async def get_product_sentiment(
    product_id: UUID,
    time_range: str = Query(default="30d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SentimentAnalysisResult:
    """Aggregate sentiment filtered by time range, with cache."""

    cache = get_cache_manager()
    cache_key = f"sentiment:{tenant_id}:{product_id}:{time_range}"

    # Try cache first
    if cache:
        cached = await cache.get(key=cache_key)
        if cached:
            return SentimentAnalysisResult(**cached)

    # DB query
    query = select(Review).where(
        Review.product_id == product_id,
        Review.tenant_id == tenant_id,
    )
    cutoff = _cutoff(time_range)
    if cutoff:
        query = query.where(Review.created_at >= cutoff)

    result = await db.execute(query)
    records = result.scalars().all()

    # If no reviews in the selected period, fall back to all-time data
    used_range = time_range
    if not records and cutoff:
        fallback_query = select(Review).where(
            Review.product_id == product_id,
            Review.tenant_id == tenant_id,
        )
        result = await db.execute(fallback_query)
        records = result.scalars().all()
        used_range = "all"

    if not records:
        empty = SentimentAnalysisResult(
            product_id=product_id,
            aggregate_sentiment=0.0,
            sentiment_distribution={"positive": 0, "negative": 0, "neutral": 0},
            top_topics=[], feature_requests=[], complaint_patterns=[],
            confidence_score=0.0, total_reviews=0,
            qa_metadata={"time_range": time_range, "note": "no reviews found"},
        )
        return empty

    total = len(records)
    counts: Dict[str, int] = {"positive": 0, "negative": 0, "neutral": 0}
    score_sum = 0.0

    for r in records:
        label = _normalize_sentiment(r.sentiment)
        counts[label] += 1
        if r.sentiment_score is not None:
            score_sum += float(r.sentiment_score)
        elif label == "positive":
            score_sum += 1.0
        elif label == "negative":
            score_sum += -1.0

    aggregate = max(-1.0, min(1.0, score_sum / total if total else 0.0))

    rating_groups: Dict[int, list] = {}
    for r in records:
        rating_groups.setdefault(r.rating, []).append(r)

    top_topics = [
        TopicCluster(
            topic_id=rating,
            keywords=[f"{rating}-star", "review"],
            review_count=len(revs),
            sample_reviews=[r.text[:100] for r in revs[:3]],
        )
        for rating, revs in sorted(rating_groups.items(), key=lambda x: -len(x[1]))[:5]
    ]

    response = SentimentAnalysisResult(
        product_id=product_id,
        aggregate_sentiment=round(aggregate, 4),
        sentiment_distribution=counts,
        top_topics=top_topics,
        feature_requests=[],
        complaint_patterns=[],
        confidence_score=round(min(1.0, total / 20.0), 3),
        total_reviews=total,
        qa_metadata={"time_range": used_range, "requested_range": time_range, "fallback": used_range == "all"},
    )

    # Store in cache — 24h TTL for sentiment data
    if cache:
        await cache.set(key=cache_key, value=response.model_dump(mode="json"), ttl=86400)

    return response


@router.get("/reviews/{product_id}")
async def get_product_reviews(
    product_id: UUID,
    time_range: str = Query(default="30d"),
    limit: int = Query(default=200),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get reviews filtered by time range, with cache."""

    cache = get_cache_manager()
    cache_key = f"reviews:{tenant_id}:{product_id}:{time_range}:{offset}:{limit}"

    if cache:
        cached = await cache.get(key=cache_key)
        if cached:
            return cached

    query = select(Review).where(
        Review.product_id == product_id,
        Review.tenant_id == tenant_id,
    )
    cutoff = _cutoff(time_range)
    if cutoff:
        query = query.where(Review.created_at >= cutoff)

    result = await db.execute(query.offset(offset).limit(limit))
    records = result.scalars().all()

    # Fall back to all-time if no reviews in selected period
    if not records and cutoff:
        fallback = select(Review).where(
            Review.product_id == product_id,
            Review.tenant_id == tenant_id,
        )
        result = await db.execute(fallback.offset(offset).limit(limit))
        records = result.scalars().all()

    payload = {
        "reviews": [
            {
                "id": str(r.id),
                "product_id": str(r.product_id),
                "rating": r.rating,
                "text": r.text,
                "sentiment": _normalize_sentiment(r.sentiment),
                "sentiment_confidence": r.sentiment_confidence,
                "is_spam": r.is_spam,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "source": r.source,
            }
            for r in records
        ],
        "total": len(records),
    }

    if cache:
        await cache.set(key=cache_key, value=payload, ttl=86400)

    return payload
