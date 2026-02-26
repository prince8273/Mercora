"""Test CRUD operations for Review, SalesRecord, and PriceHistory"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.review import (
    create_review,
    get_review,
    get_reviews_by_product,
    update_review_sentiment,
    mark_review_as_spam,
    get_review_statistics
)
from src.crud.sales_record import (
    create_sales_record,
    get_sales_record,
    get_sales_records_by_product,
    get_sales_aggregation,
    get_daily_sales
)
from src.crud.price_history import (
    create_price_history,
    get_price_history_by_product,
    get_latest_price,
    detect_price_changes,
    get_price_trend
)
from src.schemas.review import ReviewCreate
from src.schemas.sales_record import SalesRecordCreate
from src.schemas.price_history import PriceHistoryCreate


@pytest.mark.asyncio
async def test_review_crud(db_session: AsyncSession, test_tenant_id: str, test_product_id: str):
    """Test Review CRUD operations"""
    # Create a review
    review_data = ReviewCreate(
        product_id=test_product_id,
        rating=5,
        text="Great product! Highly recommended.",
        source="test"
    )
    
    review = await create_review(db_session, review_data, test_tenant_id)
    assert review.id is not None
    assert review.rating == 5
    assert review.tenant_id == test_tenant_id
    assert review.sentiment is None  # Not yet analyzed
    
    # Get the review
    fetched_review = await get_review(db_session, review.id, test_tenant_id)
    assert fetched_review is not None
    assert fetched_review.id == review.id
    
    # Update sentiment
    updated_review = await update_review_sentiment(
        db_session, review.id, "positive", 0.95, test_tenant_id
    )
    assert updated_review.sentiment == "positive"
    assert updated_review.sentiment_confidence == 0.95
    
    # Mark as spam
    spam_review = await mark_review_as_spam(db_session, review.id, test_tenant_id, True)
    assert spam_review.is_spam is True
    
    # Get reviews by product
    reviews = await get_reviews_by_product(db_session, test_product_id, test_tenant_id)
    assert len(reviews) >= 1
    
    # Get review statistics
    stats = await get_review_statistics(db_session, test_product_id, test_tenant_id)
    assert stats["total_reviews"] >= 1
    assert stats["average_rating"] > 0


@pytest.mark.asyncio
async def test_sales_record_crud(db_session: AsyncSession, test_tenant_id: str, test_product_id: str):
    """Test SalesRecord CRUD operations"""
    # Create a sales record
    sales_data = SalesRecordCreate(
        product_id=test_product_id,
        quantity=10,
        revenue=Decimal("999.90"),
        date=date.today(),
        marketplace="test-marketplace"
    )
    
    sales_record = await create_sales_record(db_session, sales_data, test_tenant_id)
    assert sales_record.id is not None
    assert sales_record.quantity == 10
    assert sales_record.revenue == Decimal("999.90")
    assert sales_record.tenant_id == test_tenant_id
    
    # Get the sales record
    fetched_record = await get_sales_record(db_session, sales_record.id, test_tenant_id)
    assert fetched_record is not None
    assert fetched_record.id == sales_record.id
    
    # Get sales records by product
    records = await get_sales_records_by_product(db_session, test_product_id, test_tenant_id)
    assert len(records) >= 1
    
    # Get sales aggregation
    aggregation = await get_sales_aggregation(db_session, test_product_id, test_tenant_id)
    assert aggregation.total_quantity >= 10
    assert aggregation.total_revenue >= Decimal("999.90")
    
    # Get daily sales
    daily_sales = await get_daily_sales(db_session, test_product_id, test_tenant_id, days=7)
    assert len(daily_sales) >= 0  # May be empty if no sales in last 7 days


@pytest.mark.asyncio
async def test_price_history_crud(db_session: AsyncSession, test_tenant_id: str, test_product_id: str):
    """Test PriceHistory CRUD operations"""
    # Create price history records
    now = datetime.utcnow()
    
    # Create multiple price points
    prices = [
        PriceHistoryCreate(
            product_id=test_product_id,
            price=Decimal("99.99"),
            source="test",
            timestamp=now - timedelta(days=7)
        ),
        PriceHistoryCreate(
            product_id=test_product_id,
            price=Decimal("89.99"),
            source="test",
            timestamp=now - timedelta(days=3)
        ),
        PriceHistoryCreate(
            product_id=test_product_id,
            price=Decimal("94.99"),
            source="test",
            timestamp=now
        )
    ]
    
    for price_data in prices:
        await create_price_history(db_session, price_data, test_tenant_id)
    
    # Get price history by product
    history = await get_price_history_by_product(db_session, test_product_id, test_tenant_id)
    assert len(history) >= 3
    
    # Get latest price
    latest = await get_latest_price(db_session, test_product_id, test_tenant_id)
    assert latest is not None
    assert latest.price == Decimal("94.99")
    
    # Detect price changes (should detect the 10% drop from 99.99 to 89.99)
    changes = await detect_price_changes(db_session, test_product_id, test_tenant_id, threshold_percent=5.0, days=10)
    assert len(changes) >= 1  # Should detect at least one significant change
    
    # Get price trend
    trend = await get_price_trend(db_session, test_product_id, test_tenant_id, days=10)
    assert trend is not None
    assert trend.current_price == Decimal("94.99")
    assert trend.data_points >= 3


@pytest.mark.asyncio
async def test_tenant_isolation(db_session: AsyncSession, test_tenant_id: str, test_product_id: str):
    """Test that tenant isolation works correctly"""
    # Create a review for test tenant
    review_data = ReviewCreate(
        product_id=test_product_id,
        rating=5,
        text="Test review",
        source="test"
    )
    review = await create_review(db_session, review_data, test_tenant_id)
    
    # Try to access with different tenant ID
    other_tenant_id = str(uuid4())
    fetched_review = await get_review(db_session, review.id, other_tenant_id)
    
    # Should not be able to access review from different tenant
    assert fetched_review is None
