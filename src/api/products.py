"""Product API endpoints"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from src.crud.product import (
    create_product,
    get_product,
    get_products,
    update_product,
    delete_product
)
from src.auth.dependencies import get_current_active_user, get_tenant_id
from src.models.user import User

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product"
)
async def create_product_endpoint(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new product with the provided data (tenant-isolated)"""
    try:
        new_product = await create_product(db, product, tenant_id)
        return new_product
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create product: {str(e)}"
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a product by ID"
)
async def get_product_endpoint(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve a product by its ID (tenant-isolated)"""
    product = await get_product(db, product_id, tenant_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    return product


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="Get a list of products"
)
async def get_products_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve a paginated list of products (tenant-isolated)"""
    products = await get_products(db, tenant_id, skip=skip, limit=limit)
    return products


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update a product"
)
async def update_product_endpoint(
    product_id: UUID,
    product: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing product with the provided data (tenant-isolated)"""
    updated_product = await update_product(db, product_id, product, tenant_id)
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    return updated_product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product"
)
async def delete_product_endpoint(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a product by its ID (tenant-isolated)"""
    deleted = await delete_product(db, product_id, tenant_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
