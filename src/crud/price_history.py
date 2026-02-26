"""CRUD operations for PriceHistory model"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.price_history import PriceHistory
from src.schemas.price_history import PriceHistoryCreate, PriceChange, PriceTrend


async def create_price_history(
    db: AsyncSession,
    price_data: PriceHistoryCreate,
    tenant_id: UUID
) -> PriceHistory:
    """Create a new price history record for a specific tenant"""
    price_history = PriceHistory(
        tenant_id=tenant_id,  # TENANT ISOLATION
        product_id=price_data.product_id,
        price=price_data.price,
        competitor_id=price_data.competitor_id,
        timestamp=price_data.timestamp or datetime.utcnow(),
        source=price_data.source
    )
    
    db.add(price_history)
    await db.flush()
    await db.refresh(price_history)
    
    return price_history


async def get_price_history(
    db: AsyncSession,
    price_history_id: UUID,
    tenant_id: UUID
) -> Optional[PriceHistory]:
    """Get a price history record by ID (tenant-filtered)"""
    result = await db.execute(
        select(PriceHistory).where(
            PriceHistory.id == price_history_id,
            PriceHistory.tenant_id == tenant_id  # TENANT ISOLATION
        )
    )
    return result.scalar_one_or_none()


async def get_price_history_by_product(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[PriceHistory]:
    """Get price history for a specific product (tenant-filtered)"""
    query = select(PriceHistory).where(
        PriceHistory.product_id == product_id,
        PriceHistory.tenant_id == tenant_id  # TENANT ISOLATION
    )
    
    if start_time:
        query = query.where(PriceHistory.timestamp >= start_time)
    
    if end_time:
        query = query.where(PriceHistory.timestamp <= end_time)
    
    query = query.offset(skip).limit(limit).order_by(PriceHistory.timestamp.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_latest_price(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID
) -> Optional[PriceHistory]:
    """Get the most recent price for a product (tenant-filtered)"""
    result = await db.execute(
        select(PriceHistory)
        .where(
            PriceHistory.product_id == product_id,
            PriceHistory.tenant_id == tenant_id  # TENANT ISOLATION
        )
        .order_by(PriceHistory.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def delete_price_history(
    db: AsyncSession,
    price_history_id: UUID,
    tenant_id: UUID
) -> bool:
    """Delete a price history record by ID (tenant-filtered)"""
    price_history = await get_price_history(db, price_history_id, tenant_id)
    if not price_history:
        return False
    
    await db.delete(price_history)
    await db.flush()
    
    return True


async def detect_price_changes(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID,
    threshold_percent: float = 5.0,
    days: int = 7
) -> List[PriceChange]:
    """Detect significant price changes for a product (tenant-filtered)"""
    # Get price history for the last N days
    start_time = datetime.utcnow() - timedelta(days=days)
    price_history = await get_price_history_by_product(
        db, product_id, tenant_id, start_time=start_time, skip=0, limit=1000
    )
    
    if len(price_history) < 2:
        return []
    
    # Sort by timestamp ascending
    price_history.sort(key=lambda x: x.timestamp)
    
    # Detect changes
    changes = []
    for i in range(1, len(price_history)):
        old_price = price_history[i-1].price
        new_price = price_history[i].price
        
        if old_price == 0:
            continue
        
        price_change = new_price - old_price
        price_change_percent = float((price_change / old_price) * 100)
        
        # Check if change exceeds threshold
        is_significant = abs(price_change_percent) >= threshold_percent
        
        if is_significant:
            changes.append(PriceChange(
                product_id=product_id,
                old_price=old_price,
                new_price=new_price,
                price_change=price_change,
                price_change_percent=price_change_percent,
                timestamp=price_history[i].timestamp,
                is_significant=is_significant
            ))
    
    return changes


async def get_price_trend(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID,
    days: int = 30
) -> Optional[PriceTrend]:
    """Analyze price trend for a product (tenant-filtered)"""
    # Get price history for the last N days
    start_time = datetime.utcnow() - timedelta(days=days)
    price_history = await get_price_history_by_product(
        db, product_id, tenant_id, start_time=start_time, skip=0, limit=1000
    )
    
    if not price_history:
        return None
    
    # Get current price (most recent)
    current_price = price_history[0].price
    
    # Calculate statistics
    prices = [float(ph.price) for ph in price_history]
    average_price = Decimal(str(sum(prices) / len(prices)))
    min_price = Decimal(str(min(prices)))
    max_price = Decimal(str(max(prices)))
    
    # Calculate volatility (standard deviation)
    mean = sum(prices) / len(prices)
    variance = sum((p - mean) ** 2 for p in prices) / len(prices)
    volatility = variance ** 0.5
    
    # Determine trend direction
    if len(price_history) >= 2:
        # Compare first half average to second half average
        mid_point = len(price_history) // 2
        first_half_avg = sum(prices[:mid_point]) / mid_point if mid_point > 0 else 0
        second_half_avg = sum(prices[mid_point:]) / (len(prices) - mid_point)
        
        if second_half_avg > first_half_avg * 1.05:  # 5% threshold
            trend_direction = "up"
        elif second_half_avg < first_half_avg * 0.95:  # 5% threshold
            trend_direction = "down"
        else:
            trend_direction = "stable"
    else:
        trend_direction = "stable"
    
    return PriceTrend(
        product_id=product_id,
        current_price=current_price,
        average_price=average_price,
        min_price=min_price,
        max_price=max_price,
        price_volatility=volatility,
        trend_direction=trend_direction,
        data_points=len(price_history)
    )


async def get_competitor_price_comparison(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID
) -> List[dict]:
    """Get latest competitor prices for comparison (tenant-filtered)"""
    # Get all price history records that have competitor_id set
    result = await db.execute(
        select(PriceHistory)
        .where(
            PriceHistory.product_id == product_id,
            PriceHistory.tenant_id == tenant_id,  # TENANT ISOLATION
            PriceHistory.competitor_id.isnot(None)
        )
        .order_by(PriceHistory.timestamp.desc())
        .limit(100)
    )
    
    competitor_prices = result.scalars().all()
    
    # Group by competitor and get latest price
    competitor_map = {}
    for ph in competitor_prices:
        if ph.competitor_id not in competitor_map:
            competitor_map[ph.competitor_id] = {
                'competitor_id': ph.competitor_id,
                'price': ph.price,
                'timestamp': ph.timestamp,
                'source': ph.source
            }
    
    return list(competitor_map.values())


async def bulk_create_price_history(
    db: AsyncSession,
    price_records: List[PriceHistoryCreate],
    tenant_id: UUID
) -> List[PriceHistory]:
    """Bulk create price history records (tenant-filtered)"""
    price_history_objects = []
    
    for price_data in price_records:
        price_history = PriceHistory(
            tenant_id=tenant_id,  # TENANT ISOLATION
            product_id=price_data.product_id,
            price=price_data.price,
            competitor_id=price_data.competitor_id,
            timestamp=price_data.timestamp or datetime.utcnow(),
            source=price_data.source
        )
        price_history_objects.append(price_history)
    
    db.add_all(price_history_objects)
    await db.flush()
    
    # Refresh all objects
    for ph in price_history_objects:
        await db.refresh(ph)
    
    return price_history_objects
