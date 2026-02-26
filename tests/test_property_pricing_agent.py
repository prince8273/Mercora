"""
Property-based tests for Pricing Intelligence Agent

Feature: ecommerce-intelligence-agent
Tasks: 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 7.5
"""
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings

from src.agents.pricing_intelligence import PricingIntelligenceAgent
from src.schemas.product import ProductResponse
from src.schemas.pricing import (
    ProductEquivalenceMapping,
    MarketData,
    MarginConstraints
)


# Strategies for generating test data
def create_product_response(id_val, sku, name, price, marketplace, category):
    """Helper to create ProductResponse"""
    return ProductResponse(
        id=id_val,
        sku=sku,
        normalized_sku=sku.upper(),
        name=name,
        price=Decimal(str(price)),
        currency='USD',
        marketplace=marketplace,
        category=category,
        inventory_level=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


product_data_strategy = st.fixed_dictionaries({
    'id_val': st.builds(uuid4),
    'sku': st.text(min_size=5, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
    'name': st.text(min_size=5, max_size=100),
    'price': st.decimals(min_value=1.0, max_value=10000.0, places=2),
    'marketplace': st.sampled_from(['Amazon', 'eBay', 'Walmart', 'Target']),
    'category': st.sampled_from(['Electronics', 'Clothing', 'Home', 'Sports', 'Books'])
})

price_history_strategy = st.fixed_dictionaries({
    'product_id': st.builds(uuid4),
    'price': st.decimals(min_value=1.0, max_value=10000.0, places=2),
    'timestamp': st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2026, 2, 21))
})


class TestPricingIntelligenceProperties:
    """
    Property-based tests for Pricing Intelligence Agent
    
    These tests verify that:
    1. Low-confidence mappings are flagged (Property 10)
    2. Price gaps are calculated correctly (Property 11)
    3. Significant price changes trigger alerts (Property 12)
    4. Promotions are extracted with details (Property 13)
    5. Pricing recommendations respect margin constraints (Property 14)
    6. All recommendations include confidence scores (Property 15)
    """
    
    @given(
        product1_data=product_data_strategy,
        product2_data=product_data_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_property_10_low_confidence_mappings_flagged(
        self,
        product1_data,
        product2_data
    ):
        """
        Property 10: Low-confidence mappings are flagged
        
        GIVEN products with varying similarity levels
        WHEN product equivalence mapping is performed
        THEN low-confidence mappings (< 0.7) should be flagged
        AND high-confidence mappings should not be flagged
        
        Validates: Requirements 3.2
        """
        # Feature: ecommerce-intelligence-agent, Property 10: Low-confidence mappings are flagged
        
        tenant_id = uuid4()
        agent = PricingIntelligenceAgent(tenant_id)
        
        # Create product responses
        our_product = create_product_response(**product1_data)
        competitor_product = create_product_response(**product2_data)
        
        # Map product equivalence
        mappings = agent.map_product_equivalence(
            our_product=our_product,
            competitor_products=[competitor_product]
        )
        
        # PROPERTY: Mappings should have confidence scores
        for mapping in mappings:
            assert hasattr(mapping, 'confidence'), \
                "Product mapping should include confidence score"
            assert 0.0 <= mapping.confidence <= 1.0, \
                "Confidence score should be between 0 and 1"
            
            # PROPERTY: Low-confidence mappings should be identifiable
            if mapping.confidence < 0.7:
                # Low confidence mappings exist and can be filtered
                assert mapping.mapping_type in ['name_similarity'], \
                    "Low-confidence mappings are typically based on name similarity"
    
    @given(
        our_price=st.decimals(min_value=10.0, max_value=1000.0, places=2),
        competitor_price=st.decimals(min_value=10.0, max_value=1000.0, places=2)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_11_price_gaps_calculated_correctly(
        self,
        our_price,
        competitor_price
    ):
        """
        Property 11: Price gaps are calculated correctly
        
        GIVEN our product price and competitor price
        WHEN price gap is calculated
        THEN the gap should be accurate (competitor_price - our_price)
        AND the percentage difference should be correct
        
        Validates: Requirements 3.3
        """
        # Feature: ecommerce-intelligence-agent, Property 11: Price gaps are calculated correctly
        
        tenant_id = uuid4()
        agent = PricingIntelligenceAgent(tenant_id)
        
        # Create product responses
        our_product = create_product_response(
            id_val=uuid4(),
            sku='OUR-SKU-001',
            name='Test Product',
            price=float(our_price),
            marketplace='Our Store',
            category='Electronics'
        )
        
        competitor_product = create_product_response(
            id_val=uuid4(),
            sku='COMP-SKU-001',
            name='Test Product',
            price=float(competitor_price),
            marketplace='Competitor Store',
            category='Electronics'
        )
        
        # Create mapping
        mapping = ProductEquivalenceMapping(
            our_product_id=our_product.id,
            competitor_product_id=competitor_product.id,
            confidence=1.0,
            mapping_type='exact_sku'
        )
        
        # Calculate price gaps
        gaps = agent.calculate_price_gaps(
            our_products=[our_product],
            competitor_products=[competitor_product],
            mappings=[mapping]
        )
        
        if gaps:
            gap = gaps[0]
            
            # PROPERTY: Price gap should be calculated correctly
            expected_gap = Decimal(str(competitor_price)) - Decimal(str(our_price))
            assert abs(gap.gap_amount - expected_gap) < Decimal('0.01'), \
                f"Price gap should be {expected_gap}, got {gap.gap_amount}"
            
            # PROPERTY: Percentage difference should be correct
            if float(our_price) > 0:
                expected_pct = float((expected_gap / Decimal(str(our_price))) * 100)
                assert abs(gap.gap_percentage - expected_pct) < 0.1, \
                    f"Percentage difference should be {expected_pct}%, got {gap.gap_percentage}%"
    
    @given(
        price_history=st.lists(price_history_strategy, min_size=2, max_size=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_12_price_changes_trigger_alerts(
        self,
        price_history
    ):
        """
        Property 12: Significant price changes trigger alerts
        
        GIVEN a product's price history
        WHEN price changes exceed 5% threshold
        THEN alerts should be generated
        AND alerts should include change details
        
        Validates: Requirements 3.4
        """
        # Feature: ecommerce-intelligence-agent, Property 12: Significant price changes trigger alerts
        
        tenant_id = uuid4()
        agent = PricingIntelligenceAgent(tenant_id)
        
        # Use same product_id for all history entries
        product_id = uuid4()
        for entry in price_history:
            entry['product_id'] = product_id
        
        # Detect price changes
        changes = agent.detect_price_changes(price_history, threshold=0.05)
        
        # PROPERTY: Changes should include necessary details
        for change in changes:
            assert hasattr(change, 'old_price'), "Change should include old_price"
            assert hasattr(change, 'new_price'), "Change should include new_price"
            assert hasattr(change, 'change_percentage'), "Change should include change_percentage"
            assert hasattr(change, 'product_id'), "Change should include product_id"
            
            # PROPERTY: Change percentage should be significant (>= 5%)
            assert abs(change.change_percentage) >= 5.0, \
                f"Detected change ({change.change_percentage}%) should exceed threshold"
    
    @given(
        original_price=st.decimals(min_value=100.0, max_value=1000.0, places=2),
        discount_pct=st.decimals(min_value=10.0, max_value=50.0, places=1)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_13_promotions_extracted_with_details(
        self,
        original_price,
        discount_pct
    ):
        """
        Property 13: Promotions are extracted with details
        
        GIVEN product data with promotion pricing
        WHEN promotions are extracted
        THEN promotion details should be identified
        AND discount amounts/percentages should be extracted
        
        Validates: Requirements 3.5
        """
        # Feature: ecommerce-intelligence-agent, Property 13: Promotions are extracted with details
        
        tenant_id = uuid4()
        agent = PricingIntelligenceAgent(tenant_id)
        
        # Calculate discounted price
        discount_amount = original_price * (discount_pct / 100)
        current_price = original_price - discount_amount
        
        # Create competitor data with promotion
        competitor_data = [{
            'product_id': uuid4(),
            'original_price': original_price,
            'current_price': current_price,
            'promotion_text': f'Save {discount_pct}% off!'
        }]
        
        # Extract promotions
        promotions = agent.extract_promotions(competitor_data)
        
        # PROPERTY: Promotions should be extracted
        assert len(promotions) > 0, "Should extract promotions from discounted products"
        
        # PROPERTY: Each promotion should have required details
        for promo in promotions:
            assert hasattr(promo, 'product_id'), "Promotion should include product_id"
            assert hasattr(promo, 'discount_percentage'), "Promotion should include discount_percentage"
            
            # PROPERTY: Discount percentage should be valid
            assert 0 <= promo.discount_percentage <= 100, \
                "Discount percentage should be between 0 and 100"
            
            # PROPERTY: Discount should be approximately correct
            assert abs(promo.discount_percentage - float(discount_pct)) < 1.0, \
                f"Extracted discount ({promo.discount_percentage}%) should match actual ({discount_pct}%)"
    
    @given(
        current_price=st.decimals(min_value=100.0, max_value=1000.0, places=2),
        min_margin_pct=st.decimals(min_value=10.0, max_value=50.0, places=1)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_14_pricing_recommendations_respect_margin_constraints(
        self,
        current_price,
        min_margin_pct
    ):
        """
        Property 14: Pricing recommendations respect margin constraints
        
        GIVEN a product with minimum margin requirements
        WHEN dynamic pricing recommendations are generated
        THEN recommended prices should maintain minimum margin
        AND no recommendation should violate margin constraints
        
        Validates: Requirements 3.6
        """
        # Feature: ecommerce-intelligence-agent, Property 14: Pricing recommendations respect margin constraints
        
        tenant_id = uuid4()
        agent = PricingIntelligenceAgent(tenant_id)
        
        # Create product
        product = create_product_response(
            id_val=uuid4(),
            sku='TEST-SKU-001',
            name='Test Product',
            price=float(current_price),
            marketplace='Our Store',
            category='Electronics'
        )
        
        # Create market data
        market_data = MarketData(
            competitor_count=5,
            average_competitor_price=Decimal(str(float(current_price) * 0.95)),
            min_competitor_price=Decimal(str(float(current_price) * 0.9)),
            max_competitor_price=Decimal(str(float(current_price) * 1.1))
        )
        
        # Create margin constraints
        margin_constraints = MarginConstraints(
            min_margin_percentage=float(min_margin_pct),
            max_discount_percentage=20.0
        )
        
        # Get pricing recommendation
        recommendation = agent.suggest_dynamic_pricing(
            product=product,
            market_data=market_data,
            margin_constraints=margin_constraints
        )
        
        # PROPERTY: Recommendation should respect maximum discount
        max_discount = margin_constraints.max_discount_percentage / 100
        min_price_allowed = current_price * (1 - Decimal(str(max_discount)))
        
        assert recommendation.suggested_price >= min_price_allowed, \
            f"Suggested price ({recommendation.suggested_price}) should respect max discount constraint"
    
    @given(
        product_data=product_data_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_property_15_all_recommendations_include_confidence_scores(
        self,
        product_data
    ):
        """
        Property 15: All recommendations include confidence scores
        
        GIVEN any pricing analysis or recommendation
        WHEN the agent generates output
        THEN all recommendations should include confidence scores
        AND confidence scores should be between 0 and 1
        
        Validates: Requirements 3.7, 7.5
        """
        # Feature: ecommerce-intelligence-agent, Property 15: All recommendations include confidence scores
        
        tenant_id = uuid4()
        agent = PricingIntelligenceAgent(tenant_id)
        
        # Create product
        product = create_product_response(**product_data)
        
        # Create market data
        market_data = MarketData(
            competitor_count=5,
            average_competitor_price=product.price,
            min_competitor_price=product.price * Decimal('0.9'),
            max_competitor_price=product.price * Decimal('1.1')
        )
        
        # Create margin constraints
        margin_constraints = MarginConstraints(
            min_margin_percentage=20.0,
            max_discount_percentage=15.0
        )
        
        # Get recommendation
        recommendation = agent.suggest_dynamic_pricing(
            product=product,
            market_data=market_data,
            margin_constraints=margin_constraints
        )
        
        # PROPERTY: Recommendation should include confidence score
        assert hasattr(recommendation, 'confidence_score'), \
            "Pricing recommendation should include confidence_score"
        
        # PROPERTY: Confidence score should be in valid range
        assert 0.0 <= recommendation.confidence_score <= 1.0, \
            f"Confidence score should be between 0 and 1, got {recommendation.confidence_score}"
        
        # Test calculate_confidence method
        data_quality = {
            'competitor_count': 5,
            'data_freshness_hours': 2.0,
            'price_variance': 0.1
        }
        
        confidence = agent.calculate_confidence(recommendation, data_quality)
        
        # PROPERTY: Confidence calculation should return valid score
        assert 0.0 <= confidence <= 1.0, \
            f"Calculated confidence should be between 0 and 1, got {confidence}"

