"""Enhanced Pricing Intelligence Agent with QA Score Integration"""
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
from src.schemas.data_quality import DataQualityReport, ProductQualityMetadata


class EnhancedPricingIntelligenceAgent:
    """
    Enhanced Pricing Intelligence Agent with Data QA Integration.
    
    Confidence Calculation:
    final_confidence = agent_confidence × data_quality_score × anomaly_penalty
    
    Where:
    - agent_confidence: Base confidence from analysis logic
    - data_quality_score: Overall quality score from QA Agent
    - anomaly_penalty: Reduction factor based on detected anomalies
    
    TENANT ISOLATION:
    All database queries are filtered by tenant_id to ensure data isolation.
    """
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize the enhanced pricing intelligence agent.
        
        Args:
            tenant_id: UUID of the tenant this agent operates for
        """
        self.tenant_id = tenant_id
        self.mapping_confidence_threshold = 0.80
        
        # Anomaly penalty factors
        self.anomaly_penalties = {
            'low': 0.95,      # 5% reduction
            'medium': 0.85,   # 15% reduction
            'high': 0.70,     # 30% reduction
            'critical': 0.50  # 50% reduction
        }
    
    def calculate_confidence_with_qa(
        self,
        base_confidence: float,
        qa_report: DataQualityReport,
        product_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Calculate final confidence incorporating QA scores and anomalies.
        
        Formula: final_confidence = base_confidence × qa_score × anomaly_penalty
        
        Args:
            base_confidence: Agent's base confidence (0-1)
            qa_report: Data quality assessment report
            product_id: Optional product ID for product-specific penalties
            
        Returns:
            Dictionary with final confidence and explanation
        """
        # Start with base confidence
        confidence = base_confidence
        
        # Apply data quality score
        qa_score = qa_report.overall_quality_score
        confidence *= qa_score
        
        # Calculate anomaly penalty
        anomaly_penalty = self._calculate_anomaly_penalty(qa_report, product_id)
        confidence *= anomaly_penalty
        
        # Build explanation
        explanation = self._build_confidence_explanation(
            base_confidence,
            qa_score,
            anomaly_penalty,
            qa_report,
            product_id
        )
        
        return {
            'final_confidence': round(confidence, 3),
            'base_confidence': round(base_confidence, 3),
            'data_quality_score': round(qa_score, 3),
            'anomaly_penalty': round(anomaly_penalty, 3),
            'explanation': explanation,
            'quality_dimensions': {
                'completeness': qa_report.dimensions.completeness.score,
                'validity': qa_report.dimensions.validity.score,
                'freshness': qa_report.dimensions.freshness.score,
                'consistency': qa_report.dimensions.consistency.score,
                'accuracy': qa_report.dimensions.accuracy.score
            }
        }
    
    def _calculate_anomaly_penalty(
        self,
        qa_report: DataQualityReport,
        product_id: Optional[UUID] = None
    ) -> float:
        """
        Calculate penalty factor based on detected anomalies.
        
        Args:
            qa_report: Quality assessment report
            product_id: Optional product ID to check for product-specific anomalies
            
        Returns:
            Penalty factor (0-1, where 1 = no penalty)
        """
        if not qa_report.anomalies:
            return 1.0
        
        # Filter anomalies relevant to this product if product_id provided
        relevant_anomalies = qa_report.anomalies
        if product_id:
            relevant_anomalies = [
                a for a in qa_report.anomalies
                if not a.affected_entities or str(product_id) in a.affected_entities
            ]
        
        if not relevant_anomalies:
            return 1.0
        
        # Apply worst penalty from relevant anomalies
        penalties = [self.anomaly_penalties.get(a.severity, 0.90) for a in relevant_anomalies]
        return min(penalties)
    
    def _build_confidence_explanation(
        self,
        base_confidence: float,
        qa_score: float,
        anomaly_penalty: float,
        qa_report: DataQualityReport,
        product_id: Optional[UUID]
    ) -> str:
        """Build human-readable confidence explanation"""
        parts = []
        
        # Base confidence
        parts.append(f"Base analysis confidence: {base_confidence:.1%}")
        
        # Data quality impact
        if qa_score < 0.9:
            impact = (1.0 - qa_score) * 100
            parts.append(f"Data quality reduced confidence by {impact:.1f}%")
            
            # Mention specific quality issues
            low_dimensions = []
            if qa_report.dimensions.completeness.score < 0.8:
                low_dimensions.append("incomplete data")
            if qa_report.dimensions.validity.score < 0.8:
                low_dimensions.append("invalid data")
            if qa_report.dimensions.freshness.score < 0.8:
                low_dimensions.append("stale data")
            
            if low_dimensions:
                parts.append(f"Issues: {', '.join(low_dimensions)}")
        
        # Anomaly impact
        if anomaly_penalty < 1.0:
            impact = (1.0 - anomaly_penalty) * 100
            parts.append(f"Detected anomalies reduced confidence by {impact:.1f}%")
            
            # Mention specific anomalies
            if product_id:
                relevant_anomalies = [
                    a for a in qa_report.anomalies
                    if str(product_id) in a.affected_entities
                ]
            else:
                relevant_anomalies = qa_report.anomalies[:2]  # Top 2
            
            for anomaly in relevant_anomalies:
                parts.append(f"⚠ {anomaly.type}: {anomaly.description}")
        
        return " | ".join(parts)
    
    def suggest_dynamic_pricing_with_qa(
        self,
        product: ProductResponse,
        market_data: MarketData,
        margin_constraints: MarginConstraints,
        qa_report: DataQualityReport
    ) -> PricingRecommendation:
        """
        Generate pricing recommendation with QA-adjusted confidence.
        
        Args:
            product: Our product
            market_data: Market analysis data
            margin_constraints: Margin constraints
            qa_report: Data quality report
            
        Returns:
            Pricing recommendation with QA-adjusted confidence
        """
        # Calculate base recommendation (existing logic)
        current_price = float(product.price)
        
        # Determine suggested price based on market position
        if market_data.average_competitor_price:
            avg_competitor = float(market_data.average_competitor_price)
            
            if current_price > avg_competitor * 1.1:
                # We're expensive - suggest reduction
                suggested_price = avg_competitor * 1.05
                action = "reduce"
                reasoning = f"Current price ${current_price:.2f} is {((current_price/avg_competitor - 1) * 100):.1f}% above market average"
            elif current_price < avg_competitor * 0.9:
                # We're cheap - suggest increase
                suggested_price = avg_competitor * 0.95
                action = "increase"
                reasoning = f"Current price ${current_price:.2f} is {((1 - current_price/avg_competitor) * 100):.1f}% below market average"
            else:
                # We're competitive - maintain
                suggested_price = current_price
                action = "maintain"
                reasoning = "Current price is competitive with market"
        else:
            suggested_price = current_price
            action = "maintain"
            reasoning = "Insufficient competitor data for recommendation"
        
        # Apply margin constraints
        suggested_price = self._apply_margin_constraints(
            suggested_price,
            current_price,
            margin_constraints
        )
        
        # Calculate base confidence
        base_confidence = self._calculate_base_confidence(market_data)
        
        # Apply QA-adjusted confidence
        confidence_data = self.calculate_confidence_with_qa(
            base_confidence,
            qa_report,
            product.id
        )
        
        # Calculate expected impact
        price_change_pct = ((suggested_price - current_price) / current_price) * 100
        expected_impact = self._estimate_impact(price_change_pct, confidence_data['final_confidence'])
        
        return PricingRecommendation(
            product_id=product.id,
            current_price=Decimal(str(current_price)),
            suggested_price=Decimal(str(suggested_price)),
            action=action,
            reasoning=reasoning,
            confidence_score=confidence_data['final_confidence'],
            expected_impact=expected_impact,
            market_position=self._determine_market_position(current_price, market_data),
            # Add QA metadata
            qa_metadata={
                'base_confidence': confidence_data['base_confidence'],
                'data_quality_score': confidence_data['data_quality_score'],
                'anomaly_penalty': confidence_data['anomaly_penalty'],
                'confidence_explanation': confidence_data['explanation'],
                'quality_dimensions': confidence_data['quality_dimensions']
            }
        )
    
    def _calculate_base_confidence(self, market_data: MarketData) -> float:
        """Calculate base confidence from market data"""
        confidence = 0.5  # Start at medium confidence
        
        # Increase confidence based on competitor count
        if market_data.competitor_count >= 5:
            confidence += 0.3
        elif market_data.competitor_count >= 3:
            confidence += 0.2
        elif market_data.competitor_count >= 1:
            confidence += 0.1
        
        # Increase confidence if we have price range data
        if market_data.min_competitor_price and market_data.max_competitor_price:
            confidence += 0.1
        
        # Increase confidence if we have average price
        if market_data.average_competitor_price:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _apply_margin_constraints(
        self,
        suggested_price: float,
        current_price: float,
        constraints: MarginConstraints
    ) -> float:
        """Apply margin constraints to suggested price"""
        max_discount = constraints.max_discount_percentage / 100.0
        min_price = current_price * (1 - max_discount)
        
        return max(min_price, suggested_price)
    
    def _estimate_impact(self, price_change_pct: float, confidence: float) -> str:
        """Estimate business impact of price change"""
        if abs(price_change_pct) < 1:
            return "Minimal impact expected"
        
        direction = "increase" if price_change_pct > 0 else "decrease"
        magnitude = "significant" if abs(price_change_pct) > 10 else "moderate"
        
        confidence_qualifier = ""
        if confidence < 0.6:
            confidence_qualifier = " (low confidence)"
        elif confidence > 0.8:
            confidence_qualifier = " (high confidence)"
        
        return f"{magnitude.capitalize()} {direction} in competitiveness expected{confidence_qualifier}"
    
    def _determine_market_position(self, current_price: float, market_data: MarketData) -> str:
        """Determine market position"""
        if not market_data.average_competitor_price:
            return "unknown"
        
        avg = float(market_data.average_competitor_price)
        
        if current_price > avg * 1.1:
            return "premium"
        elif current_price < avg * 0.9:
            return "budget"
        else:
            return "competitive"

    
    # ==================== Original Agent Methods ====================
    # These methods are copied from the original PricingIntelligenceAgent
    # to maintain compatibility with existing code
    
    def map_product_equivalence(
        self,
        our_product: ProductResponse,
        competitor_products: List[ProductResponse]
    ) -> List[ProductEquivalenceMapping]:
        """
        Map our product to equivalent competitor products.
        
        Args:
            our_product: Our product
            competitor_products: List of competitor products
            
        Returns:
            List of product equivalence mappings
        """
        mappings = []
        
        for comp_product in competitor_products:
            # Calculate similarity score
            name_similarity = self._calculate_name_similarity(
                our_product.name,
                comp_product.name
            )
            
            # Check SKU similarity
            sku_similarity = self._calculate_name_similarity(
                our_product.normalized_sku,
                comp_product.normalized_sku
            )
            
            # Combined confidence score
            confidence = (name_similarity * 0.7) + (sku_similarity * 0.3)
            
            # Only include if confidence is above threshold
            if confidence >= self.mapping_confidence_threshold:
                # Determine mapping type
                mapping_type = "exact_sku" if sku_similarity > 0.9 else "name_similarity"
                
                mapping = ProductEquivalenceMapping(
                    our_product_id=our_product.id,
                    competitor_product_id=comp_product.id,
                    confidence=confidence,
                    mapping_type=mapping_type
                )
                mappings.append(mapping)
        
        return mappings
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two product names"""
        from difflib import SequenceMatcher
        
        # Normalize names
        name1_norm = name1.lower().strip()
        name2_norm = name2.lower().strip()
        
        # Calculate sequence similarity
        similarity = SequenceMatcher(None, name1_norm, name2_norm).ratio()
        
        return similarity
    
    def calculate_price_gaps(
        self,
        our_products: List[ProductResponse],
        competitor_products: List[ProductResponse],
        mappings: List[ProductEquivalenceMapping]
    ) -> List[PriceGap]:
        """
        Calculate price gaps between our products and competitors.
        
        Args:
            our_products: Our products
            competitor_products: Competitor products
            mappings: Product equivalence mappings
            
        Returns:
            List of price gaps
        """
        price_gaps = []
        
        # Create lookup dictionaries
        our_products_dict = {p.id: p for p in our_products}
        comp_products_dict = {p.id: p for p in competitor_products}
        
        for mapping in mappings:
            our_product = our_products_dict.get(mapping.our_product_id)
            comp_product = comp_products_dict.get(mapping.competitor_product_id)
            
            if not our_product or not comp_product:
                continue
            
            # Calculate price gap
            our_price = float(our_product.price)
            comp_price = float(comp_product.price)
            
            gap_amount = our_price - comp_price
            gap_percentage = (gap_amount / comp_price) * 100 if comp_price > 0 else 0
            
            price_gap = PriceGap(
                product_id=our_product.id,
                our_price=our_product.price,
                competitor_price=comp_product.price,
                gap_amount=Decimal(str(gap_amount)),
                gap_percentage=gap_percentage,
                competitor_id=comp_product.id
            )
            price_gaps.append(price_gap)
        
        return price_gaps
    
    def detect_price_changes(
        self,
        historical_prices: List[Dict]
    ) -> List[PriceChangeAlert]:
        """
        Detect significant price changes in historical data.
        
        Args:
            historical_prices: List of historical price records
            
        Returns:
            List of price change alerts
        """
        from datetime import datetime
        
        alerts = []
        
        # Group by product
        product_prices = {}
        for record in historical_prices:
            product_id = record['product_id']
            if product_id not in product_prices:
                product_prices[product_id] = []
            product_prices[product_id].append(record)
        
        # Detect changes for each product
        for product_id, prices in product_prices.items():
            # Sort by timestamp
            prices.sort(key=lambda x: x['timestamp'])
            
            # Check for significant changes
            for i in range(1, len(prices)):
                prev_price = float(prices[i-1]['price'])
                curr_price = float(prices[i]['price'])
                
                change_amount = curr_price - prev_price
                change_percentage = (change_amount / prev_price) * 100 if prev_price > 0 else 0
                
                # Alert if change is significant (>5%)
                if abs(change_percentage) > 5:
                    timestamp = prices[i]['timestamp']
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)
                    
                    alert = PriceChangeAlert(
                        product_id=product_id,
                        old_price=Decimal(str(prev_price)),
                        new_price=Decimal(str(curr_price)),
                        change_percentage=change_percentage,
                        timestamp=timestamp,
                        competitor_id=prices[i].get('competitor_id')
                    )
                    alerts.append(alert)
        
        return alerts
    
    def extract_promotions(
        self,
        competitor_data: List[Dict]
    ) -> List[Promotion]:
        """
        Extract promotions from competitor data.
        
        Args:
            competitor_data: List of competitor data records
            
        Returns:
            List of promotions
        """
        from datetime import datetime, timedelta
        import re
        
        promotions = []
        
        for record in competitor_data:
            product_id = record.get('product_id')
            description = record.get('description', '')
            
            # Look for promotion keywords
            promo_keywords = ['sale', 'discount', 'off', 'deal', 'promo', 'special']
            has_promo = any(keyword in description.lower() for keyword in promo_keywords)
            
            if has_promo:
                # Try to extract discount percentage
                discount_match = re.search(r'(\d+)%\s*off', description, re.IGNORECASE)
                discount_percentage = float(discount_match.group(1)) if discount_match else 10.0  # Default 10%
                
                promotion = Promotion(
                    product_id=product_id,
                    discount_percentage=discount_percentage,
                    start_date=datetime.utcnow().date(),
                    end_date=(datetime.utcnow() + timedelta(days=7)).date(),  # Assume 7 days
                    description=description
                )
                promotions.append(promotion)
        
        return promotions
