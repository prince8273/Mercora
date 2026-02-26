"""Demand Forecast API endpoints"""
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from src.database import get_db
from src.models.product import Product
from src.models.sales_record import SalesRecord
from src.models.user import User
from src.agents.demand_forecast_agent import DemandForecastAgent
from src.auth.dependencies import get_current_active_user, get_tenant_id

router = APIRouter(prefix="/forecast", tags=["forecast"])


class ForecastRequest(BaseModel):
    """Request for demand forecast"""
    product_ids: List[UUID] = Field(..., description="List of product IDs to forecast")
    forecast_horizon_days: int = Field(
        default=30,
        ge=7,
        le=90,
        description="Number of days to forecast (7-90)"
    )


class ForecastResponse(BaseModel):
    """Response containing demand forecasts"""
    forecasts: List[dict]
    summary: dict


@router.post("", response_model=ForecastResponse)
async def generate_demand_forecast(
    request: ForecastRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> ForecastResponse:
    """
    Generate demand forecasts for products (TENANT-ISOLATED).
    
    This endpoint:
    1. Fetches historical sales data for the specified products
    2. Generates multi-model forecasts (ARIMA, Prophet, Exponential Smoothing)
    3. Detects seasonality and trends
    4. Generates inventory alerts
    5. Returns forecasts with confidence scores
    
    Args:
        request: Forecast request with product IDs and horizon
        db: Database session
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
        
    Returns:
        ForecastResponse with forecasts and summary
    """
    # Initialize agent (TENANT-AWARE)
    agent = DemandForecastAgent(tenant_id=tenant_id)
    
    forecasts = []
    total_alerts = 0
    products_with_insufficient_data = []
    
    for product_id in request.product_ids:
        # Fetch product (TENANT-FILTERED)
        result = await db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.tenant_id == tenant_id  # TENANT ISOLATION
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            continue
        
        # Fetch sales history (TENANT-FILTERED)
        sales_result = await db.execute(
            select(SalesRecord).where(
                SalesRecord.product_id == product_id,
                SalesRecord.tenant_id == tenant_id  # TENANT ISOLATION
            ).order_by(SalesRecord.date.asc())
        )
        sales_records = sales_result.scalars().all()
        
        if not sales_records:
            products_with_insufficient_data.append(product.name)
            continue
        
        # Convert to format expected by agent
        sales_history = [
            {
                'date': record.date,
                'quantity': record.quantity
            }
            for record in sales_records
        ]
        
        # Generate forecast
        try:
            forecast_result = agent.forecast_demand(
                product_id=product.id,
                product_name=product.name,
                sales_history=sales_history,
                forecast_horizon_days=request.forecast_horizon_days,
                current_inventory=product.inventory_level
            )
            
            forecasts.append(forecast_result.to_dict())
            total_alerts += len(forecast_result.alerts)
        
        except Exception as e:
            # Log error but continue with other products
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error forecasting for product {product.name}: {e}")
            products_with_insufficient_data.append(product.name)
    
    if not forecasts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No forecasts could be generated. Ensure products have sufficient sales history (minimum 14 days)."
        )
    
    # Generate summary
    summary = {
        "total_products_forecasted": len(forecasts),
        "total_alerts_generated": total_alerts,
        "forecast_horizon_days": request.forecast_horizon_days,
        "products_with_insufficient_data": products_with_insufficient_data,
        "average_confidence": round(
            sum(f['final_confidence'] for f in forecasts) / len(forecasts), 3
        ) if forecasts else 0.0
    }
    
    return ForecastResponse(
        forecasts=forecasts,
        summary=summary
    )


@router.get("/product/{product_id}", response_model=dict)
async def get_product_forecast(
    product_id: UUID,
    forecast_horizon_days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> dict:
    """
    Get demand forecast for a single product (TENANT-ISOLATED).
    
    Args:
        product_id: Product UUID
        forecast_horizon_days: Number of days to forecast (default: 30)
        db: Database session
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
        
    Returns:
        Forecast result dictionary
    """
    # Validate horizon
    if not (7 <= forecast_horizon_days <= 90):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forecast horizon must be between 7 and 90 days"
        )
    
    # Fetch product (TENANT-FILTERED)
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id  # TENANT ISOLATION
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
    
    # Fetch sales history (TENANT-FILTERED)
    sales_result = await db.execute(
        select(SalesRecord).where(
            SalesRecord.product_id == product_id,
            SalesRecord.tenant_id == tenant_id  # TENANT ISOLATION
        ).order_by(SalesRecord.date.asc())
    )
    sales_records = sales_result.scalars().all()
    
    if not sales_records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No sales history found for product {product.name}. Minimum 14 days of data required."
        )
    
    # Convert to format expected by agent
    sales_history = [
        {
            'date': record.date,
            'quantity': record.quantity
        }
        for record in sales_records
    ]
    
    # Initialize agent and generate forecast (TENANT-AWARE)
    agent = DemandForecastAgent(tenant_id=tenant_id)
    
    try:
        forecast_result = agent.forecast_demand(
            product_id=product.id,
            product_name=product.name,
            sales_history=sales_history,
            forecast_horizon_days=forecast_horizon_days,
            current_inventory=product.inventory_level
        )
        
        return forecast_result.to_dict()
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating forecast: {str(e)}"
        )
