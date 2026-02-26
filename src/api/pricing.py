"""Pricing intelligence API endpoints"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.product import Product
from src.models.user import User
from src.schemas.product import ProductResponse
from src.schemas.pricing import (
    PricingAnalysisRequest,
    PricingAnalysisResponse,
    MarginConstraints,
    MarketData
)
from src.agents.pricing_intelligence import PricingIntelligenceAgent
from src.auth.dependencies import get_current_active_user, get_tenant_id
from decimal import Decimal

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/analysis", response_model=PricingAnalysisResponse)
async def get_pricing_analysis(
    product_ids: str,
    include_recommendations: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> PricingAnalysisResponse:
    """
    Get pricing analysis for specified products via GET request (TENANT-ISOLATED).
    
    This is a convenience endpoint that wraps the POST /analysis endpoint.
    Product IDs should be provided as comma-separated UUIDs.
    
    Args:
        product_ids: Comma-separated list of product UUIDs
        include_recommendations: Whether to include pricing recommendations
        db: Database session
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
        
    Returns:
        Pricing analysis with gaps, changes, promotions, and recommendations
        
    Example:
        GET /api/v1/pricing/analysis?product_ids=uuid1,uuid2&include_recommendations=true
    """
    # Parse product IDs
    try:
        product_id_list = [UUID(pid.strip()) for pid in product_ids.split(',')]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format. Provide comma-separated UUIDs."
        )
    
    # Create request object
    request = PricingAnalysisRequest(
        product_ids=product_id_list,
        include_recommendations=include_recommendations
    )
    
    # Delegate to POST endpoint logic
    return await analyze_pricing(request, db, current_user, tenant_id)


@router.post("/analysis", response_model=PricingAnalysisResponse)
async def analyze_pricing(
    request: PricingAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> PricingAnalysisResponse:
    """
    Analyze pricing for specified products (TENANT-ISOLATED).
    
    Args:
        request: Pricing analysis request with product IDs and options
        db: Database session
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
        
    Returns:
        Pricing analysis with gaps, changes, promotions, and recommendations
    """
    # Initialize agent with tenant_id
    agent = PricingIntelligenceAgent(tenant_id=tenant_id)
    
    # Fetch our products (TENANT-FILTERED)
    result = await db.execute(
        select(Product).where(
            Product.id.in_(request.product_ids),
            Product.tenant_id == tenant_id  # TENANT ISOLATION
        )
    )
    products = result.scalars().all()
    
    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No products found with the specified IDs"
        )
    
    # Convert to response schemas
    our_products = [ProductResponse.model_validate(p) for p in products]
    
    # For MVP, we'll use mock competitor data
    # In production, this would fetch from competitor data sources
    competitor_products = _get_mock_competitor_products(our_products)
    
    # Create product mappings
    all_mappings = []
    for our_product in our_products:
        mappings = agent.map_product_equivalence(our_product, competitor_products)
        all_mappings.extend(mappings)
    
    # Calculate price gaps
    price_gaps = agent.calculate_price_gaps(
        our_products,
        competitor_products,
        all_mappings
    )
    
    # Detect price changes (using mock historical data for MVP)
    historical_prices = _get_mock_historical_prices(our_products, competitor_products)
    price_changes = agent.detect_price_changes(historical_prices)
    
    # Extract promotions (using mock competitor data)
    competitor_data = _get_mock_competitor_data(competitor_products)
    promotions = agent.extract_promotions(competitor_data)
    
    # Generate recommendations if requested
    recommendations = []
    if request.include_recommendations:
        margin_constraints = request.margin_constraints or MarginConstraints(
            min_margin_percentage=20.0,
            max_discount_percentage=30.0
        )
        
        for our_product in our_products:
            # Get market data for this product
            market_data = _calculate_market_data(our_product, competitor_products, all_mappings)
            
            # Generate recommendation
            recommendation = agent.suggest_dynamic_pricing(
                our_product,
                market_data,
                margin_constraints
            )
            recommendations.append(recommendation)
    
    return PricingAnalysisResponse(
        price_gaps=price_gaps,
        price_changes=price_changes,
        promotions=promotions,
        recommendations=recommendations
    )


def _get_mock_competitor_products(our_products: List[ProductResponse]) -> List[ProductResponse]:
    """
    Generate mock competitor products for MVP demonstration.
    
    In production, this would fetch from actual competitor data sources.
    """
    from datetime import datetime
    from uuid import uuid4
    
    competitor_products = []
    
    for product in our_products:
        # Create 2-3 competitor products per our product
        for i in range(2):
            competitor_price = product.price * Decimal(str(0.9 + i * 0.15))  # Vary prices
            
            competitor = ProductResponse(
                id=uuid4(),
                sku=f"COMP-{product.sku}-{i}",
                normalized_sku=product.normalized_sku if i == 0 else f"COMP-{product.normalized_sku}",
                name=product.name if i == 0 else f"{product.name} (Competitor)",
                category=product.category,
                price=competitor_price,
                currency=product.currency,
                marketplace=f"competitor_{i+1}",
                inventory_level=100,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={"is_competitor": True}
            )
            competitor_products.append(competitor)
    
    return competitor_products


def _get_mock_historical_prices(
    our_products: List[ProductResponse],
    competitor_products: List[ProductResponse]
) -> List[dict]:
    """
    Generate mock historical price data for MVP demonstration.
    """
    from datetime import datetime, timedelta
    
    historical_prices = []
    
    # Add some price changes for competitors
    for competitor in competitor_products[:2]:  # Just first 2 for demo
        # Old price (7 days ago)
        old_price = competitor.price * Decimal('1.08')  # 8% higher
        historical_prices.append({
            'product_id': competitor.id,
            'price': old_price,
            'timestamp': datetime.utcnow() - timedelta(days=7),
            'competitor_id': competitor.id
        })
        
        # Current price
        historical_prices.append({
            'product_id': competitor.id,
            'price': competitor.price,
            'timestamp': datetime.utcnow(),
            'competitor_id': competitor.id
        })
    
    return historical_prices


def _get_mock_competitor_data(competitor_products: List[ProductResponse]) -> List[dict]:
    """
    Generate mock competitor promotion data for MVP demonstration.
    """
    from datetime import date, timedelta
    
    competitor_data = []
    
    # Add promotions for some competitors
    for i, competitor in enumerate(competitor_products[:2]):
        if i == 0:  # First competitor has a promotion
            competitor_data.append({
                'product_id': competitor.id,
                'original_price': competitor.price * Decimal('1.15'),
                'current_price': competitor.price,
                'promotion_text': "15% off sale",
                'start_date': date.today() - timedelta(days=3),
                'end_date': date.today() + timedelta(days=4)
            })
        else:
            competitor_data.append({
                'product_id': competitor.id,
                'current_price': competitor.price
            })
    
    return competitor_data


def _calculate_market_data(
    our_product: ProductResponse,
    competitor_products: List[ProductResponse],
    mappings: List
) -> MarketData:
    """
    Calculate market data for a product based on competitor prices.
    """
    # Find competitor products mapped to our product
    competitor_ids = [
        m.competitor_product_id
        for m in mappings
        if m.our_product_id == our_product.id
    ]
    
    competitor_prices = [
        p.price
        for p in competitor_products
        if p.id in competitor_ids
    ]
    
    if not competitor_prices:
        # No competitors, use our price as reference
        competitor_prices = [our_product.price]
    
    avg_price = sum(competitor_prices) / len(competitor_prices)
    min_price = min(competitor_prices)
    max_price = max(competitor_prices)
    
    return MarketData(
        competitor_count=len(competitor_prices),
        average_competitor_price=avg_price,
        min_competitor_price=min_price,
        max_competitor_price=max_price,
        price_trend="stable"
    )
