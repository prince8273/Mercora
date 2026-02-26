"""CRUD operations for Product model"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.product import Product
from src.schemas.product import ProductCreate, ProductUpdate
from src.cache.event_bus import get_event_publisher, DataEvent, EventType


def normalize_sku(sku: str) -> str:
    """Normalize SKU to uppercase alphanumeric format"""
    # Remove non-alphanumeric characters and convert to uppercase
    return ''.join(c for c in sku if c.isalnum()).upper()


async def create_product(
    db: AsyncSession,
    product_data: ProductCreate,
    tenant_id: UUID
) -> Product:
    """Create a new product for a specific tenant"""
    # Normalize the SKU
    normalized_sku = normalize_sku(product_data.sku)
    
    # Create product instance
    product = Product(
        tenant_id=tenant_id,  # TENANT ISOLATION
        sku=product_data.sku,
        normalized_sku=normalized_sku,
        name=product_data.name,
        category=product_data.category,
        price=product_data.price,
        currency=product_data.currency,
        marketplace=product_data.marketplace,
        inventory_level=product_data.inventory_level,
        extra_metadata=product_data.metadata
    )
    
    db.add(product)
    await db.flush()
    await db.refresh(product)
    
    # Publish event for cache invalidation
    try:
        publisher = get_event_publisher()
        event = DataEvent(
            event_type=EventType.PRODUCT_CREATED,
            tenant_id=tenant_id,
            entity_type='product',
            entity_id=str(product.id)
        )
        await publisher.publish(event)
    except Exception as e:
        # Log but don't fail the operation
        import logging
        logging.getLogger(__name__).warning(f"Failed to publish product created event: {e}")
    
    return product


async def get_product(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID
) -> Optional[Product]:
    """Get a product by ID (tenant-filtered)"""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id  # TENANT ISOLATION
        )
    )
    return result.scalar_one_or_none()


async def get_products(
    db: AsyncSession,
    tenant_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Product]:
    """Get a list of products with pagination (tenant-filtered)"""
    result = await db.execute(
        select(Product)
        .where(Product.tenant_id == tenant_id)  # TENANT ISOLATION
        .offset(skip)
        .limit(limit)
        .order_by(Product.created_at.desc())
    )
    return list(result.scalars().all())


async def update_product(
    db: AsyncSession,
    product_id: UUID,
    product_data: ProductUpdate,
    tenant_id: UUID
) -> Optional[Product]:
    """Update an existing product (tenant-filtered)"""
    # Get the product (with tenant check)
    product = await get_product(db, product_id, tenant_id)
    if not product:
        return None
    
    # Update fields that are provided
    update_data = product_data.model_dump(exclude_unset=True)
    
    # If SKU is being updated, recalculate normalized_sku
    if 'sku' in update_data:
        update_data['normalized_sku'] = normalize_sku(update_data['sku'])
    
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await db.flush()
    await db.refresh(product)
    
    # Publish event for cache invalidation
    try:
        publisher = get_event_publisher()
        event = DataEvent(
            event_type=EventType.PRODUCT_UPDATED,
            tenant_id=tenant_id,
            entity_type='product',
            entity_id=str(product_id)
        )
        await publisher.publish(event)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to publish product updated event: {e}")
    
    return product


async def delete_product(
    db: AsyncSession,
    product_id: UUID,
    tenant_id: UUID
) -> bool:
    """Delete a product by ID (tenant-filtered)"""
    product = await get_product(db, product_id, tenant_id)
    if not product:
        return False
    
    await db.delete(product)
    await db.flush()
    
    # Publish event for cache invalidation
    try:
        publisher = get_event_publisher()
        event = DataEvent(
            event_type=EventType.PRODUCT_DELETED,
            tenant_id=tenant_id,
            entity_type='product',
            entity_id=str(product_id)
        )
        await publisher.publish(event)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to publish product deleted event: {e}")
    
    return True
