"""CRUD operations for SalesRecord model"""
from typing import List, Optional
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.sales_record import SalesRecord
from src.schemas.sales_record import SalesRecordCreate, SalesRecordUpdate, SalesAggregation


async def create_sales_record(
    db: AsyncSession,
    sales_data: SalesRecordCreate,
    tenant_id: UUID
) -> SalesRecord:
    """Create a new sales record for a specific tenant"""
    sales_record = SalesRecord(
        tenant_id=tenant_id,  # TENANT ISOLATION
        product_id=sales_data.product_id,
        quantity=sales_data.quantity,
        revenue=sales_data.revenue,
        date=sales_data.date,
        marketplace=sales_data.marketplace,
        extra_data=sales_data.metadata
    )
    
    db.add(sales_record)
    await db.flush()
    await db.refresh(sales_record)
    
    return sales_record


async def get_sales_record(
    db: AsyncSession,
    sales_record_id: UUID,
    tenant_id: UUID
) -> Optional[SalesRecord]:
    """Get a sales record by ID (tenant-filtered)"""
    result = await db.execute(
        select(SalesRecord).where(
            SalesRecord.id == sales_record_id,
            SalesRecord.tenant_id == tenant_id  # TENANT ISOLATION
        )
    )
    return result.scalar_one_or_none()


async def get_sales_records_by_product(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[SalesRecord]:
    """Get sales records for a specific product (tenant-filtered)"""
    query = select(SalesRecord).where(
        SalesRecord.product_id == product_id,
        SalesRecord.tenant_id == tenant_id  # TENANT ISOLATION
    )
    
    if start_date:
        query = query.where(SalesRecord.date >= start_date)
    
    if end_date:
        query = query.where(SalesRecord.date <= end_date)
    
    query = query.offset(skip).limit(limit).order_by(SalesRecord.date.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_sales_records(
    db: AsyncSession,
    tenant_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    marketplace: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[SalesRecord]:
    """Get sales records with optional filtering (tenant-filtered)"""
    query = select(SalesRecord).where(SalesRecord.tenant_id == tenant_id)  # TENANT ISOLATION
    
    if start_date:
        query = query.where(SalesRecord.date >= start_date)
    
    if end_date:
        query = query.where(SalesRecord.date <= end_date)
    
    if marketplace:
        query = query.where(SalesRecord.marketplace == marketplace)
    
    query = query.offset(skip).limit(limit).order_by(SalesRecord.date.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_sales_record(
    db: AsyncSession,
    sales_record_id: UUID,
    sales_data: SalesRecordUpdate,
    tenant_id: UUID
) -> Optional[SalesRecord]:
    """Update an existing sales record (tenant-filtered)"""
    sales_record = await get_sales_record(db, sales_record_id, tenant_id)
    if not sales_record:
        return None
    
    # Update fields that are provided
    update_data = sales_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        # Map 'metadata' to 'extra_data' for the model
        if field == 'metadata':
            setattr(sales_record, 'extra_data', value)
        else:
            setattr(sales_record, field, value)
    
    await db.flush()
    await db.refresh(sales_record)
    
    return sales_record


async def delete_sales_record(
    db: AsyncSession,
    sales_record_id: UUID,
    tenant_id: UUID
) -> bool:
    """Delete a sales record by ID (tenant-filtered)"""
    sales_record = await get_sales_record(db, sales_record_id, tenant_id)
    if not sales_record:
        return False
    
    await db.delete(sales_record)
    await db.flush()
    
    return True


async def get_sales_aggregation(
    db: AsyncSession,
    product_id: Optional[UUID],
    tenant_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> SalesAggregation:
    """Get aggregated sales data for a product or all products (tenant-filtered)"""
    query = select(
        func.sum(SalesRecord.quantity).label('total_quantity'),
        func.sum(SalesRecord.revenue).label('total_revenue'),
        func.count(SalesRecord.id).label('record_count'),
        func.min(SalesRecord.date).label('min_date'),
        func.max(SalesRecord.date).label('max_date')
    ).where(SalesRecord.tenant_id == tenant_id)  # TENANT ISOLATION
    
    if product_id:
        query = query.where(SalesRecord.product_id == product_id)
    
    if start_date:
        query = query.where(SalesRecord.date >= start_date)
    
    if end_date:
        query = query.where(SalesRecord.date <= end_date)
    
    result = await db.execute(query)
    row = result.one()
    
    total_quantity = row.total_quantity or 0
    total_revenue = row.total_revenue or Decimal('0.00')
    record_count = row.record_count or 0
    
    # Calculate average revenue per sale
    average_revenue = total_revenue / record_count if record_count > 0 else Decimal('0.00')
    
    # Use provided dates or actual data range
    date_range_start = start_date or row.min_date or date.today()
    date_range_end = end_date or row.max_date or date.today()
    
    return SalesAggregation(
        total_quantity=total_quantity,
        total_revenue=total_revenue,
        average_revenue_per_sale=average_revenue,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
        record_count=record_count
    )


async def get_daily_sales(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID,
    days: int = 30
) -> List[dict]:
    """Get daily sales aggregation for the last N days (tenant-filtered)"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Get all sales records in the date range
    sales_records = await get_sales_records_by_product(
        db, product_id, tenant_id, start_date, end_date, skip=0, limit=10000
    )
    
    # Aggregate by date
    daily_sales = {}
    for record in sales_records:
        record_date = record.date
        if record_date not in daily_sales:
            daily_sales[record_date] = {
                'date': record_date,
                'quantity': 0,
                'revenue': Decimal('0.00')
            }
        
        daily_sales[record_date]['quantity'] += record.quantity
        daily_sales[record_date]['revenue'] += record.revenue
    
    # Convert to list and sort by date
    result = sorted(daily_sales.values(), key=lambda x: x['date'])
    
    return result
