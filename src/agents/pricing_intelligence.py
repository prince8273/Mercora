"""Pricing Intelligence Agent for competitive pricing analysis"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
from difflib import SequenceMatcher

from src.schemas.pricing import (
    PriceGap,
    PriceChangeAlert,
    Promotion,
    PricingRecommendation,
    MarginConstraints,
    MarketData,
    ProductEquivalenceMapping
)
from src.schemas.product import ProductResponse


class PricingIntelligenceAgent:
    """
    Analyzes competitive pricing and generates recommendations.
    
    MVP Simplified Scope:
    - Simple product equivalence mapping (exact SKU match or name similarity)
    - Basic confidence scoring
    - No complex ML models for MVP
    
    TENANT ISOLATION:
    All database queries are filtered by tenant_id to ensure data isolation.
    """
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize the pricing intelligence agent.
        
        Args:
            tenant_id: UUID of the tenant this agent operates for
        """
        self.tenant_id = tenant_id
        self.mapping_confidence_threshold = 0.80
    
    def calculate_price_gaps(
        self,
        our_products: List[ProductResponse],
        competitor_products: List[ProductResponse],
        mappings: List[ProductEquivalenceMapping]
    ) -> List[PriceGap]:
        """
        Calculate price gaps between our products and competitor equivalents.
        
        Args:
            our_products: List of our products
            competitor_products: List of competitor products
            mappings: Product equivalence mappings
            
        Returns:
            List of price gaps
        """
        price_gaps = []
        
        # Create lookup dictionaries
        our_products_dict = {p.id: p for p in our_products}
        competitor_products_dict = {p.id: p for p in competitor_products}
        
        for mapping in mappings:
            our_product = our_products_dict.get(mapping.our_product_id)
            competitor_product = competitor_products_dict.get(mapping.competitor_product_id)
            
            if not our_product or not competitor_product:
                continue
            
            # Calculate gap
            gap_amount = competitor_product.price - our_product.price
            gap_percentage = float((gap_amount / our_product.price) * 100) if our_product.price > 0 else 0.0
            
            price_gap = PriceGap(
                product_id=our_product.id,
                our_price=our_product.price,
                competitor_price=competitor_product.price,
                gap_amount=gap_amount,
                gap_percentage=gap_percentage,
                competitor_id=competitor_product.id
            )
            price_gaps.append(price_gap)
        
        return price_gaps
    
    def detect_price_changes(
        self,
        historical_prices: List[Dict[str, Any]],
        threshold: float = 0.05
    ) -> List[PriceChangeAlert]:
        """
        Detect significant price changes (>5% by default).
        
        Args:
            historical_prices: List of price history records with keys:
                - product_id: UUID
                - price: Decimal
                - timestamp: datetime
                - competitor_id: Optional[UUID]
            threshold: Minimum percentage change to trigger alert (default 0.05 = 5%)
            
        Returns:
            List of price change alerts
        """
        alerts = []
        
        # Group by product_id
        price_by_product: Dict[UUID, List[Dict[str, Any]]] = {}
        for record in historical_prices:
            product_id = record.get('product_id')
            if product_id:
                if product_id not in price_by_product:
                    price_by_product[product_id] = []
                price_by_product[product_id].append(record)
        
        # Detect changes for each product
        for product_id, prices in price_by_product.items():
            # Sort by timestamp
            sorted_prices = sorted(prices, key=lambda x: x.get('timestamp', datetime.min))
            
            # Compare consecutive prices
            for i in range(1, len(sorted_prices)):
                old_record = sorted_prices[i - 1]
                new_record = sorted_prices[i]
                
                old_price = old_record.get('price')
                new_price = new_record.get('price')
                
                if not old_price or not new_price or old_price == 0:
                    continue
                
                # Calculate percentage change
                change = (new_price - old_price) / old_price
                change_percentage = float(change * 100)
                
                # Check if change exceeds threshold
                if abs(change) > threshold:
                    alert = PriceChangeAlert(
                        product_id=product_id,
                        old_price=old_price,
                        new_price=new_price,
                        change_percentage=change_percentage,
                        timestamp=new_record.get('timestamp', datetime.utcnow()),
                        competitor_id=new_record.get('competitor_id')
                    )
                    alerts.append(alert)
        
        return alerts
    
    def extract_promotions(
        self,
        competitor_data: List[Dict[str, Any]]
    ) -> List[Promotion]:
        """
        Extract promotion details from competitor data.
        
        Args:
            competitor_data: List of competitor product data with keys:
                - product_id: UUID
                - original_price: Optional[Decimal]
                - current_price: Decimal
                - promotion_text: Optional[str]
                - start_date: Optional[date]
                - end_date: Optional[date]
                
        Returns:
            List of promotions
        """
        promotions = []
        
        for data in competitor_data:
            product_id = data.get('product_id')
            original_price = data.get('original_price')
            current_price = data.get('current_price')
            
            if not product_id or not current_price:
                continue
            
            # Calculate discount if original price is available
            discount_percentage = 0.0
            if original_price and original_price > 0 and current_price < original_price:
                discount = (original_price - current_price) / original_price
                discount_percentage = float(discount * 100)
            
            # Only create promotion if there's a discount
            if discount_percentage > 0:
                promotion = Promotion(
                    product_id=product_id,
                    discount_percentage=discount_percentage,
                    start_date=data.get('start_date'),
                    end_date=data.get('end_date'),
                    description=data.get('promotion_text')
                )
                promotions.append(promotion)
        
        return promotions
    
    def suggest_dynamic_pricing(
        self,
        product: ProductResponse,
        market_data: MarketData,
        margin_constraints: MarginConstraints,
        data_quality_score: float = 1.0,
        anomaly_penalty: float = 1.0
    ) -> PricingRecommendation:
        """
        Generate dynamic pricing recommendation based on market data and constraints.
        
        Args:
            product: Our product
            market_data: Market pricing data
            margin_constraints: Margin and discount constraints
            
        Returns:
            Pricing recommendation
        """
        current_price = product.price
        
        # Simple pricing strategy for MVP:
        # 1. If we're above average, suggest moving closer to average
        # 2. If we're below average, maintain or increase slightly
        # 3. Respect margin constraints
        
        avg_price = market_data.average_competitor_price
        min_price = market_data.min_competitor_price
        max_price = market_data.max_competitor_price
        
        # Calculate suggested price
        if current_price > avg_price:
            # We're expensive, move toward average
            suggested_price = (current_price + avg_price) / 2
            reasoning = f"Current price (${current_price}) is above market average (${avg_price}). Suggesting price reduction to improve competitiveness."
        elif current_price < avg_price:
            # We're cheap, can potentially increase
            suggested_price = min(current_price * Decimal('1.05'), avg_price)
            reasoning = f"Current price (${current_price}) is below market average (${avg_price}). Suggesting slight increase to improve margins."
        else:
            # We're at average, maintain
            suggested_price = current_price
            reasoning = f"Current price (${current_price}) is at market average. Maintaining current pricing."
        
        # Apply margin constraints
        max_discount = margin_constraints.max_discount_percentage / 100
        min_price_allowed = current_price * (1 - Decimal(str(max_discount)))
        
        if suggested_price < min_price_allowed:
            suggested_price = min_price_allowed
            reasoning += f" Adjusted to respect maximum discount constraint of {margin_constraints.max_discount_percentage}%."
        
        # Calculate confidence and expected impact
        base_confidence = self._calculate_pricing_confidence(product, market_data)
        
        # Apply tiered confidence formula:
        # final_confidence = agent_confidence × data_quality_score × anomaly_penalty
        final_confidence = base_confidence * data_quality_score * anomaly_penalty
        final_confidence = max(0.0, min(1.0, final_confidence))  # Clamp to [0, 1]
        
        expected_impact = self._estimate_pricing_impact(
            current_price,
            suggested_price,
            market_data
        )
        
        # Add quality metadata to reasoning if confidence was adjusted
        if data_quality_score < 1.0 or anomaly_penalty < 1.0:
            quality_note = f" [Confidence adjusted: base={base_confidence:.2f}, quality={data_quality_score:.2f}, anomaly_penalty={anomaly_penalty:.2f}]"
            reasoning += quality_note
        
        return PricingRecommendation(
            product_id=product.id,
            current_price=current_price,
            suggested_price=suggested_price,
            reasoning=reasoning,
            confidence_score=final_confidence,
            expected_impact=expected_impact
        )
    
    def calculate_confidence(
        self,
        recommendation: PricingRecommendation,
        data_quality: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for a pricing recommendation.
        
        Args:
            recommendation: The pricing recommendation
            data_quality: Data quality metrics with keys:
                - competitor_count: int
                - data_freshness_hours: float
                - price_variance: float
                
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 1.0
        
        # Reduce confidence based on competitor count
        competitor_count = data_quality.get('competitor_count', 0)
        if competitor_count < 3:
            confidence *= 0.7
        elif competitor_count < 5:
            confidence *= 0.85
        
        # Reduce confidence based on data freshness
        data_freshness_hours = data_quality.get('data_freshness_hours', 0)
        if data_freshness_hours > 24:
            confidence *= 0.8
        elif data_freshness_hours > 12:
            confidence *= 0.9
        
        # Reduce confidence based on price variance
        price_variance = data_quality.get('price_variance', 0)
        if price_variance > 0.3:  # High variance
            confidence *= 0.75
        elif price_variance > 0.15:  # Medium variance
            confidence *= 0.9
        
        return max(0.0, min(1.0, confidence))
    
    def map_product_equivalence(
        self,
        our_product: ProductResponse,
        competitor_products: List[ProductResponse]
    ) -> List[ProductEquivalenceMapping]:
        """
        Create product equivalence mappings using exact SKU match or name similarity.
        
        Args:
            our_product: Our product
            competitor_products: List of competitor products
            
        Returns:
            List of product equivalence mappings
        """
        mappings = []
        
        for competitor_product in competitor_products:
            # Try exact SKU match first
            if our_product.normalized_sku == competitor_product.normalized_sku:
                mapping = ProductEquivalenceMapping(
                    our_product_id=our_product.id,
                    competitor_product_id=competitor_product.id,
                    confidence=1.0,
                    mapping_type="exact_sku"
                )
                mappings.append(mapping)
            else:
                # Try name similarity
                similarity = self._calculate_name_similarity(
                    our_product.name,
                    competitor_product.name
                )
                
                # Only create mapping if similarity is above threshold
                if similarity >= 0.5:
                    confidence = 0.5 + (similarity - 0.5) * 0.8  # Scale to 0.5-0.9
                    mapping = ProductEquivalenceMapping(
                        our_product_id=our_product.id,
                        competitor_product_id=competitor_product.id,
                        confidence=confidence,
                        mapping_type="name_similarity"
                    )
                    mappings.append(mapping)
        
        return mappings
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two product names.
        
        Args:
            name1: First product name
            name2: Second product name
            
        Returns:
            Similarity score between 0 and 1
        """
        # Normalize names
        name1_normalized = name1.lower().strip()
        name2_normalized = name2.lower().strip()
        
        # Use SequenceMatcher for similarity
        similarity = SequenceMatcher(None, name1_normalized, name2_normalized).ratio()
        
        return similarity
    
    def _calculate_pricing_confidence(
        self,
        product: ProductResponse,
        market_data: MarketData
    ) -> float:
        """
        Calculate confidence for pricing recommendation.
        
        Args:
            product: The product
            market_data: Market data
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 1.0
        
        # Reduce confidence if few competitors
        competitor_count = market_data.competitor_count
        if competitor_count < 3:
            confidence *= 0.7
        elif competitor_count < 5:
            confidence *= 0.85
        
        # Reduce confidence if high price variance (based on min/max spread)
        if (market_data.average_competitor_price and 
            market_data.min_competitor_price and 
            market_data.max_competitor_price):
            avg = market_data.average_competitor_price
            price_range = float(market_data.max_competitor_price - market_data.min_competitor_price)
            relative_variance = price_range / float(avg) if float(avg) > 0 else 0
            
            if relative_variance > 0.3:
                confidence *= 0.75
            elif relative_variance > 0.15:
                confidence *= 0.9
        
        return max(0.0, min(1.0, confidence))
    
    def _estimate_pricing_impact(
        self,
        current_price: Decimal,
        suggested_price: Decimal,
        market_data: MarketData
    ) -> str:
        """
        Estimate the impact of price change.
        
        Args:
            current_price: Current price
            suggested_price: Suggested price
            market_data: Market data
            
        Returns:
            String describing the expected impact
        """
        price_change_pct = float((suggested_price - current_price) / current_price * 100) if current_price > 0 else 0.0
        
        # Simple impact estimation for MVP
        # Assume -1% price = +2% demand (price elasticity of -2)
        estimated_demand_change_pct = -price_change_pct * 2
        
        # Estimate revenue impact (simplified)
        estimated_revenue_change_pct = price_change_pct + estimated_demand_change_pct
        
        market_position = self._determine_market_position(suggested_price, market_data)
        
        # Format as string
        return (
            f"Price change: {price_change_pct:+.2f}%, "
            f"Estimated demand change: {estimated_demand_change_pct:+.2f}%, "
            f"Estimated revenue change: {estimated_revenue_change_pct:+.2f}%, "
            f"Market position: {market_position}"
        )
    
    def _determine_market_position(
        self,
        price: Decimal,
        market_data: MarketData
    ) -> str:
        """
        Determine market position based on price.
        
        Args:
            price: The price to evaluate
            market_data: Market data
            
        Returns:
            Market position description
        """
        avg = market_data.average_competitor_price
        
        if not avg:
            return "unknown"
        
        if price < avg * Decimal('0.9'):
            return "budget"
        elif price > avg * Decimal('1.1'):
            return "premium"
        else:
            return "competitive"
