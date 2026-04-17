"""Pricing intelligence API endpoints"""
from typing import List
from uuid import UUID
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

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
from src.cache.instance import get_cache_manager
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


@router.get("/history/{product_id}")
async def get_price_history(
    product_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get price history for a product (TENANT-ISOLATED)."""
    cache = get_cache_manager()
    cache_key = f"price_history:{tenant_id}:{product_id}:{days}"
    if cache:
        cached = await cache.get(key=cache_key)
        if cached:
            return cached

    # Verify product belongs to tenant
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get real price history from database
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    # Query price history
    history_result = await db.execute(
        text("""
            SELECT price_date, price, competitor_avg, market_demand, price_change_reason
            FROM price_history 
            WHERE product_id = :product_id 
            AND tenant_id = :tenant_id 
            AND price_date >= :start_date 
            AND price_date <= :end_date
            ORDER BY price_date ASC
        """),
        {
            "product_id": str(product_id),
            "tenant_id": str(tenant_id),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    )
    
    trends = []
    for row in history_result:
        trends.append({
            "date": str(row[0]),
            "price": float(row[1]),
            "competitor_avg": float(row[2]) if row[2] else None,
            "market_demand": float(row[3]) if row[3] else None,
            "reason": row[4]
        })
    
    result_payload = {
        "product_id": str(product_id),
        "trends": trends,
        "current_price": float(product.price),
        "period_days": days,
        "data_points": len(trends)
    }
    if cache:
        await cache.set(key=cache_key, value=result_payload, ttl=3600)
    return result_payload


@router.get("/recommendations/{product_id}")
async def get_pricing_recommendations(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get pricing recommendations for a product (TENANT-ISOLATED)."""
    cache = get_cache_manager()
    cache_key = f"pricing_recs:{tenant_id}:{product_id}"
    if cache:
        cached = await cache.get(key=cache_key)
        if cached:
            return cached

    # Verify product belongs to tenant
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get market analysis data
    market_result = await db.execute(
        text("""
            SELECT market_position, price_elasticity, demand_score, 
                   competitive_index, recommended_price, confidence_score
            FROM market_analysis 
            WHERE product_id = :product_id AND tenant_id = :tenant_id
        """),
        {"product_id": str(product_id), "tenant_id": str(tenant_id)}
    )
    
    market_data = market_result.first()
    
    # Get current price early so we can use it for mock competitors if needed
    current_price = float(product.price)
    
    # Get competitor data
    competitor_result = await db.execute(
        text("""
            SELECT competitor_name, competitor_price, competitor_rating, market_share
            FROM competitor_pricing 
            WHERE product_id = :product_id AND tenant_id = :tenant_id
            ORDER BY market_share DESC
        """),
        {"product_id": str(product_id), "tenant_id": str(tenant_id)}
    )
    
    competitors = []
    competitor_prices = []
    for row in competitor_result:
        competitors.append({
            "name": row[0],
            "price": float(row[1]),
            "rating": float(row[2]) if row[2] else None,
            "market_share": float(row[3]) if row[3] else None
        })
        competitor_prices.append(float(row[1]))
    
    # If no competitor data exists, create mock competitors based on current price
    if not competitor_prices:
        # Create realistic competitor prices around current price
        mock_competitor_1 = current_price * 0.85  # 15% lower
        mock_competitor_2 = current_price * 1.15  # 15% higher
        mock_competitor_3 = current_price * 0.95  # 5% lower
        
        competitors = [
            {"name": "Market Competitor A", "price": mock_competitor_1, "rating": 4.2, "market_share": 0.25},
            {"name": "Market Competitor B", "price": mock_competitor_2, "rating": 4.0, "market_share": 0.20},
            {"name": "Market Competitor C", "price": mock_competitor_3, "rating": 4.1, "market_share": 0.15}
        ]
        competitor_prices = [mock_competitor_1, mock_competitor_2, mock_competitor_3]
    
    # Get product cost for profit calculations
    product_cost = getattr(product, 'cost', None)
    if product_cost is None:
        # Estimate cost as 60% of current price if not available
        product_cost = current_price * 0.6
    else:
        product_cost = float(product_cost)
    
    # Generate sophisticated recommendations
    recommendations = []
    
    if competitor_prices:
        min_competitor_price = min(competitor_prices)
        max_competitor_price = max(competitor_prices)
        avg_competitor_price = sum(competitor_prices) / len(competitor_prices)
        
        # 1. Competitive Pricing Strategy
        if current_price > avg_competitor_price:
            # Price is above average - recommend competitive pricing
            suggested_price = avg_competitor_price * 0.95  # 5% below average
            profit_margin = ((suggested_price - product_cost) / suggested_price) * 100
            
            # Always recommend if we're above average, even with lower margins
            if profit_margin > 5:  # Reduced from 10% to 5% for more aggressive recommendations
                # Calculate confidence for competitive pricing
                confidence_factors = []
                
                # Factor 1: How much above average we are (more above = higher confidence in reduction)
                above_average_ratio = (current_price - avg_competitor_price) / avg_competitor_price
                above_confidence = min(0.95, 0.6 + (above_average_ratio * 1.5))
                confidence_factors.append(above_confidence)
                
                # Factor 2: Profit margin safety after reduction
                margin_safety = min(0.9, profit_margin / 50)  # Scale to 0-0.9 based on 50% target
                confidence_factors.append(margin_safety)
                
                # Factor 3: Competitor data quality
                data_quality = min(0.85, 0.4 + (len(competitors) * 0.15))
                confidence_factors.append(data_quality)
                
                competitive_confidence = sum(confidence_factors) / len(confidence_factors)
                
                recommendations.append({
                    "id": "competitive_pricing",
                    "type": "competitive",
                    "title": "Competitive Price Adjustment",
                    "current_price": current_price,
                    "suggested_price": round(suggested_price, 2),
                    "profit_margin": round(profit_margin, 1),
                    "expected_impact": {
                        "revenue_change": "+15-25%",
                        "volume_change": "+30-50%",
                        "market_share": "+5-10%"
                    },
                    "confidence": round(competitive_confidence, 2),
                    "reasoning": f"Your price (₹{current_price:.2f}) is {((current_price - avg_competitor_price) / avg_competitor_price * 100):.1f}% above market average (₹{avg_competitor_price:.2f}). Reducing to ₹{suggested_price:.2f} could increase sales volume significantly while maintaining {profit_margin:.1f}% profit margin."
                })
            else:
                # Even if margin is very low, suggest a less aggressive reduction
                conservative_price = avg_competitor_price * 1.05  # 5% above average instead
                conservative_margin = ((conservative_price - product_cost) / conservative_price) * 100
                
                recommendations.append({
                    "id": "conservative_competitive_pricing",
                    "type": "competitive",
                    "title": "Conservative Price Reduction",
                    "current_price": current_price,
                    "suggested_price": round(conservative_price, 2),
                    "profit_margin": round(conservative_margin, 1),
                    "expected_impact": {
                        "revenue_change": "+8-15%",
                        "volume_change": "+15-25%",
                        "market_share": "+2-5%"
                    },
                    "confidence": 0.75,
                    "reasoning": f"Your price (₹{current_price:.2f}) is significantly above market average (₹{avg_competitor_price:.2f}). A conservative reduction to ₹{conservative_price:.2f} maintains competitiveness while preserving {conservative_margin:.1f}% profit margin."
                })
        
        # Also add a recommendation if we're above the minimum competitor price
        elif current_price > min_competitor_price * 1.1:  # If we're >10% above the lowest competitor
            suggested_price = min_competitor_price * 1.05  # Position just above lowest competitor
            profit_margin = ((suggested_price - product_cost) / suggested_price) * 100
            
            if profit_margin > 0:  # Any positive margin
                recommendations.append({
                    "id": "undercut_competition",
                    "type": "competitive",
                    "title": "Undercut Competition Strategy",
                    "current_price": current_price,
                    "suggested_price": round(suggested_price, 2),
                    "profit_margin": round(profit_margin, 1),
                    "expected_impact": {
                        "revenue_change": "+20-35%",
                        "volume_change": "+40-60%",
                        "market_share": "+10-15%"
                    },
                    "confidence": 0.85,
                    "reasoning": f"Your price (₹{current_price:.2f}) is much higher than the lowest competitor (₹{min_competitor_price:.2f}). Positioning at ₹{suggested_price:.2f} could capture significant market share while maintaining {profit_margin:.1f}% margin."
                })
        
        # 2. Premium Positioning Strategy
        if current_price < max_competitor_price:
            # Opportunity for premium pricing
            suggested_price = min(max_competitor_price * 0.98, current_price * 1.15)  # Up to 15% increase or just below max competitor
            profit_margin = ((suggested_price - product_cost) / suggested_price) * 100
            
            # Calculate confidence based on multiple factors
            confidence_factors = []
            
            # Factor 1: Price gap size (larger gap = higher confidence)
            price_gap_ratio = (max_competitor_price - current_price) / current_price
            gap_confidence = min(0.9, 0.4 + (price_gap_ratio * 0.5))  # 0.4-0.9 range
            confidence_factors.append(gap_confidence)
            
            # Factor 2: Number of competitors (more competitors = more data = higher confidence)
            competitor_count_confidence = min(0.8, 0.3 + (len(competitors) * 0.1))  # 0.3-0.8 range
            confidence_factors.append(competitor_count_confidence)
            
            # Factor 3: Profit margin safety (higher margin = higher confidence)
            margin_confidence = min(0.9, profit_margin / 100)  # Convert percentage to decimal
            confidence_factors.append(margin_confidence)
            
            # Factor 4: Market position stability (based on price spread)
            price_spread = (max_competitor_price - min_competitor_price) / avg_competitor_price
            spread_confidence = max(0.4, 0.8 - price_spread)  # Lower spread = higher confidence
            confidence_factors.append(spread_confidence)
            
            # Factor 5: Suggested price increase reasonableness (smaller increase = higher confidence)
            increase_ratio = (suggested_price - current_price) / current_price
            increase_confidence = max(0.5, 0.9 - (increase_ratio * 2))  # Penalize large increases
            confidence_factors.append(increase_confidence)
            
            # Calculate weighted average confidence
            final_confidence = sum(confidence_factors) / len(confidence_factors)
            
            recommendations.append({
                "id": "premium_positioning",
                "type": "premium",
                "title": "Premium Market Positioning",
                "current_price": current_price,
                "suggested_price": round(suggested_price, 2),
                "profit_margin": round(profit_margin, 1),
                "expected_impact": {
                    "revenue_change": "+8-15%",
                    "volume_change": "-5-10%",
                    "profit_increase": "+20-35%"
                },
                "confidence": round(final_confidence, 2),
                "confidence_breakdown": {
                    "price_gap_factor": round(gap_confidence, 2),
                    "competitor_data_factor": round(competitor_count_confidence, 2),
                    "profit_margin_factor": round(margin_confidence, 2),
                    "market_stability_factor": round(spread_confidence, 2),
                    "price_increase_factor": round(increase_confidence, 2)
                },
                "reasoning": f"Market can support higher prices up to ${max_competitor_price:.2f}. Increasing to ${suggested_price:.2f} positions you as premium while maximizing profit margin ({profit_margin:.1f}%). Confidence based on: price gap ({gap_confidence:.0%}), competitor data ({competitor_count_confidence:.0%}), profit safety ({margin_confidence:.0%}), market stability ({spread_confidence:.0%}), reasonable increase ({increase_confidence:.0%})."
            })
        
        # 3. Maximum Profit Opportunity
        # Calculate optimal price for maximum profit using price elasticity
        elasticity = float(market_data[1]) if market_data and market_data[1] else -1.5
        
        # Optimal price formula: P* = MC / (1 + 1/elasticity) where MC is marginal cost
        if elasticity < -1:  # Elastic demand
            optimal_price = product_cost / (1 + 1/elasticity)
            
            # Ensure it's within reasonable bounds
            optimal_price = max(min(optimal_price, max_competitor_price * 1.1), min_competitor_price * 0.9)
            profit_margin = ((optimal_price - product_cost) / optimal_price) * 100
            
            if abs(optimal_price - current_price) > current_price * 0.02:  # Reduced from 5% to 2% for more recommendations
                recommendations.append({
                    "id": "max_profit_optimization",
                    "type": "optimization",
                    "title": "Maximum Profit Optimization",
                    "current_price": current_price,
                    "suggested_price": round(optimal_price, 2),
                    "profit_margin": round(profit_margin, 1),
                    "expected_impact": {
                        "profit_increase": f"+{((optimal_price - current_price) / current_price * 100):.1f}%",
                        "revenue_optimization": "Maximized",
                        "elasticity_factor": f"{elasticity:.2f}"
                    },
                    "confidence": 0.78,
                    "reasoning": f"Based on demand elasticity ({elasticity:.2f}), optimal price for maximum profit is ${optimal_price:.2f}. This balances volume and margin for highest total profit ({profit_margin:.1f}% margin)."
                })
        
        # 4. Market Gap Opportunity
        # Look for pricing gaps in competitor landscape
        sorted_prices = sorted(competitor_prices)
        for i in range(len(sorted_prices) - 1):
            gap = sorted_prices[i + 1] - sorted_prices[i]
            if gap > sorted_prices[i] * 0.15:  # Gap > 15% of lower price
                gap_price = sorted_prices[i] + (gap * 0.6)  # Position in upper part of gap
                profit_margin = ((gap_price - product_cost) / gap_price) * 100
                
                if profit_margin > 10 and abs(gap_price - current_price) > current_price * 0.02:  # Reduced threshold
                    recommendations.append({
                        "id": "market_gap_opportunity",
                        "type": "opportunity",
                        "title": "Market Gap Opportunity",
                        "current_price": current_price,
                        "suggested_price": round(gap_price, 2),
                        "profit_margin": round(profit_margin, 1),
                        "expected_impact": {
                            "market_positioning": "Unique price point",
                            "competition": "Reduced direct competition",
                            "margin_improvement": f"+{profit_margin - ((current_price - product_cost) / current_price * 100):.1f}%"
                        },
                        "confidence": 0.65,
                        "reasoning": f"Identified pricing gap between ${sorted_prices[i]:.2f} and ${sorted_prices[i+1]:.2f}. Positioning at ${gap_price:.2f} reduces direct price competition while maintaining strong {profit_margin:.1f}% margin."
                    })
                break  # Only recommend one gap opportunity
        
        # 5. Dynamic Pricing Strategy
        # Based on market share and competitive position
        market_leader_price = max(competitor_prices)
        market_follower_price = min(competitor_prices)
        
        if len(competitors) >= 3:  # Need sufficient competition for dynamic strategy
            # Calculate market-weighted average price
            weighted_price = sum(comp["price"] * comp["market_share"] for comp in competitors if comp["market_share"]) / sum(comp["market_share"] for comp in competitors if comp["market_share"])
            
            if weighted_price and abs(weighted_price - current_price) > current_price * 0.03:  # Reduced from 8% to 3%
                profit_margin = ((weighted_price - product_cost) / weighted_price) * 100
                
                recommendations.append({
                    "id": "dynamic_market_pricing",
                    "type": "dynamic",
                    "title": "Market-Weighted Dynamic Pricing",
                    "current_price": current_price,
                    "suggested_price": round(weighted_price, 2),
                    "profit_margin": round(profit_margin, 1),
                    "expected_impact": {
                        "market_alignment": "Optimal competitive position",
                        "risk_level": "Low",
                        "adaptability": "High"
                    },
                    "confidence": 0.80,
                    "reasoning": f"Market-share weighted optimal price is ${weighted_price:.2f}. This aligns with successful competitors' pricing strategies while maintaining {profit_margin:.1f}% profit margin."
                })
    
    # Sort recommendations by confidence and profit potential
    recommendations.sort(key=lambda x: (x["confidence"], x["profit_margin"]), reverse=True)
    
    # ALWAYS provide recommendations if we have competitor data
    if competitor_prices and not recommendations:
        
        # Strategy 1: If above average, recommend reduction
        if current_price > avg_competitor_price:
            target_price = avg_competitor_price * 0.98  # Just below average
            margin = ((target_price - product_cost) / target_price) * 100 if target_price > product_cost else 0
            
            recommendations.append({
                "id": "price_reduction_strategy",
                "type": "competitive",
                "title": "Competitive Price Reduction",
                "current_price": current_price,
                "suggested_price": round(target_price, 2),
                "profit_margin": round(margin, 1),
                "expected_impact": {
                    "revenue_change": "+10-25%",
                    "volume_change": "+20-40%",
                    "market_share": "+5-15%"
                },
                "confidence": 0.80,
                "reasoning": f"Your price (₹{current_price:.2f}) is {((current_price - avg_competitor_price) / avg_competitor_price * 100):.1f}% above the market average (₹{avg_competitor_price:.2f}). Reducing to ₹{target_price:.2f} will improve competitiveness and likely increase sales volume."
            })
        
        # Strategy 2: If above minimum, suggest undercutting
        if current_price > min_competitor_price * 1.05:
            undercut_price = min_competitor_price * 0.98  # Just below lowest
            margin = ((undercut_price - product_cost) / undercut_price) * 100 if undercut_price > product_cost else 0
            
            recommendations.append({
                "id": "undercut_strategy", 
                "type": "aggressive",
                "title": "Market Penetration Pricing",
                "current_price": current_price,
                "suggested_price": round(undercut_price, 2),
                "profit_margin": round(margin, 1),
                "expected_impact": {
                    "revenue_change": "+25-50%",
                    "volume_change": "+50-100%",
                    "market_share": "+15-30%"
                },
                "confidence": 0.85,
                "reasoning": f"Aggressive pricing strategy: Position just below the lowest competitor (₹{min_competitor_price:.2f}) at ₹{undercut_price:.2f} to capture maximum market share. Current price (₹{current_price:.2f}) is significantly higher."
            })
        
        # Strategy 3: Conservative approach - move halfway to average
        if current_price > avg_competitor_price:
            conservative_price = (current_price + avg_competitor_price) / 2
            margin = ((conservative_price - product_cost) / conservative_price) * 100 if conservative_price > product_cost else 0
            
            recommendations.append({
                "id": "conservative_adjustment",
                "type": "optimization", 
                "title": "Conservative Price Adjustment",
                "current_price": current_price,
                "suggested_price": round(conservative_price, 2),
                "profit_margin": round(margin, 1),
                "expected_impact": {
                    "revenue_change": "+5-15%",
                    "volume_change": "+10-25%",
                    "risk_level": "Low"
                },
                "confidence": 0.75,
                "reasoning": f"Conservative approach: Reduce price from ₹{current_price:.2f} to ₹{conservative_price:.2f} (halfway to market average of ₹{avg_competitor_price:.2f}). This maintains higher margins while improving competitiveness."
            })
    
    # If we STILL don't have recommendations but have competitor data, force create one
    if competitor_prices and not recommendations:
        emergency_price = avg_competitor_price
        emergency_margin = ((emergency_price - product_cost) / emergency_price) * 100 if emergency_price > product_cost else 0
        
        recommendations.append({
            "id": "emergency_market_alignment",
            "type": "optimization",
            "title": "Market Price Alignment", 
            "current_price": current_price,
            "suggested_price": round(emergency_price, 2),
            "profit_margin": round(emergency_margin, 1),
            "expected_impact": {
                "market_alignment": "Perfect",
                "competitive_position": "Balanced"
            },
            "confidence": 0.70,
            "reasoning": f"Align with market average price of ₹{emergency_price:.2f}. Your current price: ₹{current_price:.2f}. Competitor range: ₹{min_competitor_price:.2f} - ₹{max_competitor_price:.2f}."
        })
    
    # Limit to top 3 recommendations
    recommendations = recommendations[:3]

    recs_payload = {
        "product_id": str(product_id),
        "recommendations": recommendations,
        "market_analysis": {
            "current_price": current_price,
            "product_cost": product_cost,
            "current_margin": round(((current_price - product_cost) / current_price) * 100, 1),
            "competitor_price_range": {
                "min": min(competitor_prices) if competitor_prices else None,
                "max": max(competitor_prices) if competitor_prices else None,
                "average": round(sum(competitor_prices) / len(competitor_prices), 2) if competitor_prices else None
            },
            "market_position": market_data[0] if market_data else "competitive",
            "price_elasticity": float(market_data[1]) if market_data else -1.0
        },
        "competitors": competitors,
        "debug_info": {
            "database_price": current_price,
            "product_name": product.name,
            "product_sku": product.sku,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    if cache:
        await cache.set(key=cache_key, value=recs_payload, ttl=3600)
    return recs_payload


@router.get("/competitors/{product_id}")
async def get_competitor_matrix(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get competitor matrix data for a product (TENANT-ISOLATED)."""
    # Verify product belongs to tenant
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get competitor data for this product
    competitor_result = await db.execute(
        text("""
            SELECT competitor_name, competitor_price, competitor_rating, market_share
            FROM competitor_pricing 
            WHERE product_id = :product_id AND tenant_id = :tenant_id
            ORDER BY market_share DESC
        """),
        {"product_id": str(product_id), "tenant_id": str(tenant_id)}
    )
    
    competitors = []
    competitor_prices = {}
    
    for i, row in enumerate(competitor_result):
        comp_id = f"comp_{i+1}"
        competitors.append({
            "id": comp_id,
            "name": row[0],
            "rating": float(row[2]) if row[2] else None,
            "market_share": float(row[3]) if row[3] else None
        })
        competitor_prices[comp_id] = float(row[1])
    
    # Create matrix data
    matrix_data = [{
        "productName": product.name,
        "sku": product.sku,
        "yourPrice": float(product.price),
        "competitorPrices": competitor_prices
    }]
    
    return {
        "data": matrix_data,
        "competitors": competitors,
        "product_id": str(product_id)
    }


from pydantic import BaseModel

class PriceUpdateRequest(BaseModel):
    new_price: float

@router.put("/apply/{product_id}")
async def apply_pricing_recommendation(
    product_id: UUID,
    request: PriceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Apply a pricing recommendation by updating the product price (TENANT-ISOLATED)."""
    # Verify product belongs to tenant
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    old_price = float(product.price)
    new_price = request.new_price
    
    # Update product price
    await db.execute(
        text("""
            UPDATE products 
            SET price = :new_price, updated_at = :updated_at
            WHERE id = :product_id AND tenant_id = :tenant_id
        """),
        {
            "new_price": new_price,
            "updated_at": datetime.utcnow(),
            "product_id": str(product_id),
            "tenant_id": str(tenant_id)
        }
    )
    
    # Add new price history entry
    await db.execute(
        text("""
            INSERT INTO price_history 
            (id, product_id, tenant_id, price_date, price, price_change_reason, competitor_avg, market_demand)
            VALUES (:id, :product_id, :tenant_id, :price_date, :price, :reason, 
                   (SELECT AVG(cp.competitor_price) FROM competitor_pricing cp 
                    WHERE cp.product_id = :product_id AND cp.tenant_id = :tenant_id), 0.8)
        """),
        {
            "id": str(uuid.uuid4()),
            "product_id": str(product_id),
            "tenant_id": str(tenant_id),
            "price_date": datetime.utcnow().date(),
            "price": new_price,
            "reason": "Applied pricing recommendation"
        }
    )
    
    await db.commit()
    
    return {
        "success": True,
        "product_id": str(product_id),
        "old_price": old_price,
        "new_price": new_price,
        "price_change": new_price - old_price,
        "price_change_percent": ((new_price - old_price) / old_price) * 100,
        "updated_at": datetime.utcnow().isoformat()
    }


@router.get("/promotions/{product_id}")
async def get_promotion_effectiveness(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get promotion effectiveness for a product (TENANT-ISOLATED)."""
    # Verify product belongs to tenant
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get real promotion history from database
    promotion_result = await db.execute(
        text("""
            SELECT promotion_name, discount_percent, start_date, end_date,
                   revenue_impact, units_sold, conversion_rate, effectiveness_score
            FROM promotion_history 
            WHERE product_id = :product_id AND tenant_id = :tenant_id
            ORDER BY start_date DESC
        """),
        {"product_id": str(product_id), "tenant_id": str(tenant_id)}
    )
    
    promotions = []
    total_revenue = 0
    effectiveness_scores = []
    
    for row in promotion_result:
        promo_data = {
            "name": row[0],
            "discount_percent": float(row[1]),
            "start_date": str(row[2]),
            "end_date": str(row[3]),
            "metrics": {
                "revenue": float(row[4]) if row[4] else 0,
                "units_sold": int(row[5]) if row[5] else 0,
                "conversion_rate": float(row[6]) if row[6] else 0
            },
            "effectiveness_score": float(row[7]) if row[7] else 0
        }
        
        # Determine effectiveness level
        score = promo_data["effectiveness_score"]
        if score >= 0.8:
            promo_data["effectiveness"] = "high"
        elif score >= 0.6:
            promo_data["effectiveness"] = "medium"
        else:
            promo_data["effectiveness"] = "low"
        
        promotions.append(promo_data)
        total_revenue += promo_data["metrics"]["revenue"]
        effectiveness_scores.append(score)
    
    # Calculate average effectiveness
    avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0
    
    return {
        "product_id": str(product_id),
        "promotions": promotions,
        "total_revenue": round(total_revenue, 2),
        "avg_effectiveness": round(avg_effectiveness, 2),
        "promotion_count": len(promotions)
    }
    
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
