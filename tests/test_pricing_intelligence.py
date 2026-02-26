"""Tests for Pricing Intelligence Agent"""
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.agents.pricing_intelligence import PricingIntelligenceAgent
from src.schemas.pricing import (
    MarginConstraints,
    MarketData,
    ProductEquivalenceMapping
)
from src.schemas.product import ProductResponse


@pytest.fixture
def agent():
    """Create a pricing intelligence agent instance"""
    tenant_id = uuid4()
    return PricingIntelligenceAgent(tenant_id=tenant_id)


@pytest.fixture
def sample_product():
    """Create a sample product"""
    return ProductResponse(
        id=uuid4(),
        sku="TEST-001",
        normalized_sku="TEST001",
        name="Test Product",
        category="Electronics",
        price=Decimal("99.99"),
        currency="USD",
        marketplace="our_store",
        inventory_level=50,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata={}
    )


@pytest.fixture
def competitor_products():
    """Create sample competitor products"""
    return [
        ProductResponse(
            id=uuid4(),
            sku="COMP-001",
            normalized_sku="TEST001",  # Same normalized SKU for exact match
            name="Test Product",
            category="Electronics",
            price=Decimal("95.00"),
            currency="USD",
            marketplace="competitor_1",
            inventory_level=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"is_competitor": True}
        ),
        ProductResponse(
            id=uuid4(),
            sku="COMP-002",
            normalized_sku="COMP002",
            name="Test Product Pro",  # Similar name
            category="Electronics",
            price=Decimal("105.00"),
            currency="USD",
            marketplace="competitor_2",
            inventory_level=75,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"is_competitor": True}
        ),
        ProductResponse(
            id=uuid4(),
            sku="COMP-003",
            normalized_sku="COMP003",
            name="Different Product",  # Different name
            category="Electronics",
            price=Decimal("89.99"),
            currency="USD",
            marketplace="competitor_3",
            inventory_level=60,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"is_competitor": True}
        )
    ]


class TestProductEquivalenceMapping:
    """Tests for product equivalence mapping"""
    
    def test_exact_sku_match(self, agent, sample_product, competitor_products):
        """Test exact SKU matching produces confidence 1.0"""
        mappings = agent.map_product_equivalence(sample_product, competitor_products)
        
        # Should find exact match with first competitor
        exact_matches = [m for m in mappings if m.mapping_type == "exact_sku"]
        assert len(exact_matches) == 1
        assert exact_matches[0].confidence == 1.0
        assert exact_matches[0].competitor_product_id == competitor_products[0].id
    
    def test_name_similarity_match(self, agent, sample_product, competitor_products):
        """Test name similarity matching"""
        mappings = agent.map_product_equivalence(sample_product, competitor_products)
        
        # Should find similarity match with second competitor
        similarity_matches = [m for m in mappings if m.mapping_type == "name_similarity"]
        assert len(similarity_matches) >= 1
        
        # Confidence should be between 0.5 and 0.9
        for match in similarity_matches:
            assert 0.5 <= match.confidence <= 0.9
    
    def test_low_similarity_rejected(self, agent, sample_product, competitor_products):
        """Test that low similarity products are not mapped"""
        mappings = agent.map_product_equivalence(sample_product, competitor_products)
        
        # Third competitor has very different name, should not be mapped or have lower confidence
        competitor_3_mappings = [
            m for m in mappings
            if m.competitor_product_id == competitor_products[2].id
        ]
        # Should either not exist or have confidence below 0.7
        if competitor_3_mappings:
            assert competitor_3_mappings[0].confidence < 0.7


class TestPriceGapCalculation:
    """Tests for price gap calculation"""
    
    def test_calculate_price_gaps(self, agent, sample_product, competitor_products):
        """Test price gap calculation"""
        # Create mappings
        mappings = [
            ProductEquivalenceMapping(
                our_product_id=sample_product.id,
                competitor_product_id=competitor_products[0].id,
                confidence=1.0,
                mapping_type="exact_sku"
            ),
            ProductEquivalenceMapping(
                our_product_id=sample_product.id,
                competitor_product_id=competitor_products[1].id,
                confidence=0.8,
                mapping_type="name_similarity"
            )
        ]
        
        price_gaps = agent.calculate_price_gaps(
            [sample_product],
            competitor_products,
            mappings
        )
        
        assert len(price_gaps) == 2
        
        # Check first gap (competitor is cheaper)
        gap1 = price_gaps[0]
        assert gap1.product_id == sample_product.id
        assert gap1.our_price == Decimal("99.99")
        assert gap1.competitor_price == Decimal("95.00")
        assert gap1.gap_amount == Decimal("-4.99")
        assert gap1.gap_percentage < 0  # We're more expensive
        
        # Check second gap (competitor is more expensive)
        gap2 = price_gaps[1]
        assert gap2.competitor_price == Decimal("105.00")
        assert gap2.gap_amount == Decimal("5.01")
        assert gap2.gap_percentage > 0  # We're cheaper
    
    def test_price_gap_percentage_calculation(self, agent, sample_product, competitor_products):
        """Test price gap percentage is calculated correctly"""
        mappings = [
            ProductEquivalenceMapping(
                our_product_id=sample_product.id,
                competitor_product_id=competitor_products[0].id,
                confidence=1.0,
                mapping_type="exact_sku"
            )
        ]
        
        price_gaps = agent.calculate_price_gaps(
            [sample_product],
            competitor_products,
            mappings
        )
        
        gap = price_gaps[0]
        expected_percentage = float((Decimal("95.00") - Decimal("99.99")) / Decimal("99.99") * 100)
        assert abs(gap.gap_percentage - expected_percentage) < 0.01


class TestPriceChangeDetection:
    """Tests for price change detection"""
    
    def test_detect_significant_price_changes(self, agent):
        """Test detection of price changes above threshold"""
        product_id = uuid4()
        historical_prices = [
            {
                'product_id': product_id,
                'price': Decimal("100.00"),
                'timestamp': datetime.utcnow() - timedelta(days=7)
            },
            {
                'product_id': product_id,
                'price': Decimal("110.00"),  # 10% increase
                'timestamp': datetime.utcnow()
            }
        ]
        
        alerts = agent.detect_price_changes(historical_prices, threshold=0.05)
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.product_id == product_id
        assert alert.old_price == Decimal("100.00")
        assert alert.new_price == Decimal("110.00")
        assert abs(alert.change_percentage - 10.0) < 0.01
    
    def test_ignore_small_price_changes(self, agent):
        """Test that small price changes below threshold are ignored"""
        product_id = uuid4()
        historical_prices = [
            {
                'product_id': product_id,
                'price': Decimal("100.00"),
                'timestamp': datetime.utcnow() - timedelta(days=7)
            },
            {
                'product_id': product_id,
                'price': Decimal("102.00"),  # 2% increase
                'timestamp': datetime.utcnow()
            }
        ]
        
        alerts = agent.detect_price_changes(historical_prices, threshold=0.05)
        
        assert len(alerts) == 0
    
    def test_detect_price_decrease(self, agent):
        """Test detection of price decreases"""
        product_id = uuid4()
        historical_prices = [
            {
                'product_id': product_id,
                'price': Decimal("100.00"),
                'timestamp': datetime.utcnow() - timedelta(days=7)
            },
            {
                'product_id': product_id,
                'price': Decimal("85.00"),  # 15% decrease
                'timestamp': datetime.utcnow()
            }
        ]
        
        alerts = agent.detect_price_changes(historical_prices, threshold=0.05)
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.change_percentage < 0  # Negative for decrease
        assert abs(alert.change_percentage - (-15.0)) < 0.01


class TestPromotionExtraction:
    """Tests for promotion extraction"""
    
    def test_extract_promotions_with_discount(self, agent):
        """Test extraction of promotions with discount"""
        product_id = uuid4()
        competitor_data = [
            {
                'product_id': product_id,
                'original_price': Decimal("100.00"),
                'current_price': Decimal("80.00"),
                'promotion_text': "20% off sale",
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=7)
            }
        ]
        
        promotions = agent.extract_promotions(competitor_data)
        
        assert len(promotions) == 1
        promo = promotions[0]
        assert promo.product_id == product_id
        assert abs(promo.discount_percentage - 20.0) < 0.01
        assert promo.description == "20% off sale"
        assert promo.start_date == date.today()
    
    def test_no_promotion_without_discount(self, agent):
        """Test that no promotion is created without a discount"""
        product_id = uuid4()
        competitor_data = [
            {
                'product_id': product_id,
                'current_price': Decimal("100.00")
            }
        ]
        
        promotions = agent.extract_promotions(competitor_data)
        
        assert len(promotions) == 0
    
    def test_no_promotion_when_price_increased(self, agent):
        """Test that no promotion is created when price increased"""
        product_id = uuid4()
        competitor_data = [
            {
                'product_id': product_id,
                'original_price': Decimal("80.00"),
                'current_price': Decimal("100.00")  # Price went up
            }
        ]
        
        promotions = agent.extract_promotions(competitor_data)
        
        assert len(promotions) == 0


class TestDynamicPricing:
    """Tests for dynamic pricing suggestions"""
    
    def test_suggest_price_reduction_when_above_average(self, agent, sample_product):
        """Test price reduction suggestion when above market average"""
        market_data = MarketData(
            competitor_count=3,
            average_competitor_price=Decimal("87.67"),
            min_competitor_price=Decimal("85.00"),
            max_competitor_price=Decimal("90.00"),
            price_trend="stable"
        )
        
        margin_constraints = MarginConstraints(
            min_margin_percentage=20.0,
            max_discount_percentage=30.0
        )
        
        recommendation = agent.suggest_dynamic_pricing(
            sample_product,
            market_data,
            margin_constraints
        )
        
        assert recommendation.product_id == sample_product.id
        assert recommendation.current_price == Decimal("99.99")
        assert recommendation.suggested_price < Decimal("99.99")
        assert recommendation.confidence_score > 0
        assert "above market average" in recommendation.reasoning.lower()
    
    def test_suggest_price_increase_when_below_average(self, agent, sample_product):
        """Test price increase suggestion when below market average"""
        # Modify product to have lower price
        low_price_product = ProductResponse(
            **{**sample_product.model_dump(), 'price': Decimal("75.00")}
        )
        
        market_data = MarketData(
            competitor_count=3,
            average_competitor_price=Decimal("97.67"),
            min_competitor_price=Decimal("95.00"),
            max_competitor_price=Decimal("100.00"),
            price_trend="stable"
        )
        
        margin_constraints = MarginConstraints(
            min_margin_percentage=20.0,
            max_discount_percentage=30.0
        )
        
        recommendation = agent.suggest_dynamic_pricing(
            low_price_product,
            market_data,
            margin_constraints
        )
        
        assert recommendation.suggested_price > Decimal("75.00")
        assert "below market average" in recommendation.reasoning.lower()
    
    def test_respect_margin_constraints(self, agent, sample_product):
        """Test that pricing recommendations respect margin constraints"""
        market_data = MarketData(
            competitor_count=2,
            average_competitor_price=Decimal("52.50"),
            min_competitor_price=Decimal("50.00"),
            max_competitor_price=Decimal("55.00"),
            price_trend="stable"
        )
        
        # Very restrictive constraint - max 10% discount
        margin_constraints = MarginConstraints(
            min_margin_percentage=20.0,
            max_discount_percentage=10.0
        )
        
        recommendation = agent.suggest_dynamic_pricing(
            sample_product,
            market_data,
            margin_constraints
        )
        
        # Should not discount more than 10%
        min_allowed_price = Decimal("99.99") * Decimal("0.90")
        assert recommendation.suggested_price >= min_allowed_price
        assert "constraint" in recommendation.reasoning.lower()
    
    def test_expected_impact_calculation(self, agent, sample_product):
        """Test that expected impact is calculated"""
        market_data = MarketData(
            competitor_count=1,
            average_competitor_price=Decimal("95.00"),
            min_competitor_price=Decimal("95.00"),
            max_competitor_price=Decimal("95.00"),
            price_trend="stable"
        )
        
        margin_constraints = MarginConstraints(
            min_margin_percentage=20.0,
            max_discount_percentage=30.0
        )
        
        recommendation = agent.suggest_dynamic_pricing(
            sample_product,
            market_data,
            margin_constraints
        )
        
        # expected_impact should be a string
        assert isinstance(recommendation.expected_impact, str)
        assert "price change" in recommendation.expected_impact.lower()
        assert "demand change" in recommendation.expected_impact.lower()
        assert "revenue change" in recommendation.expected_impact.lower()
        assert "market position" in recommendation.expected_impact.lower()


class TestConfidenceScoring:
    """Tests for confidence score calculation"""
    
    def test_high_confidence_with_good_data(self, agent, sample_product):
        """Test high confidence with good data quality"""
        market_data = MarketData(
            competitor_count=5,
            average_competitor_price=Decimal("97.00"),
            min_competitor_price=Decimal("95.00"),
            max_competitor_price=Decimal("99.00"),
            price_trend="stable"
        )
        
        margin_constraints = MarginConstraints(
            min_margin_percentage=20.0,
            max_discount_percentage=30.0
        )
        
        recommendation = agent.suggest_dynamic_pricing(
            sample_product,
            market_data,
            margin_constraints
        )
        
        # Should have high confidence with 5 competitors and low variance
        assert recommendation.confidence_score > 0.8
    
    def test_low_confidence_with_few_competitors(self, agent, sample_product):
        """Test lower confidence with few competitors"""
        market_data = MarketData(
            competitor_count=1,
            average_competitor_price=Decimal("95.00"),
            min_competitor_price=Decimal("95.00"),
            max_competitor_price=Decimal("95.00"),
            price_trend="stable"
        )
        
        margin_constraints = MarginConstraints(
            min_margin_percentage=20.0,
            max_discount_percentage=30.0
        )
        
        recommendation = agent.suggest_dynamic_pricing(
            sample_product,
            market_data,
            margin_constraints
        )
        
        # Should have lower confidence with only 1 competitor
        assert recommendation.confidence_score < 0.8
    
    def test_confidence_with_data_quality_metrics(self, agent):
        """Test confidence calculation with data quality metrics"""
        from src.schemas.pricing import PricingRecommendation
        
        recommendation = PricingRecommendation(
            product_id=uuid4(),
            current_price=Decimal("100.00"),
            suggested_price=Decimal("95.00"),
            reasoning="Test",
            confidence_score=0.9,
            expected_impact="Test impact"
        )
        
        # Good data quality
        data_quality = {
            'competitor_count': 5,
            'data_freshness_hours': 2,
            'price_variance': 0.1
        }
        
        confidence = agent.calculate_confidence(recommendation, data_quality)
        assert confidence > 0.8
        
        # Poor data quality
        poor_data_quality = {
            'competitor_count': 1,
            'data_freshness_hours': 30,
            'price_variance': 0.5
        }
        
        low_confidence = agent.calculate_confidence(recommendation, poor_data_quality)
        assert low_confidence < 0.6


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_empty_competitor_list(self, agent, sample_product):
        """Test handling of empty competitor list"""
        mappings = agent.map_product_equivalence(sample_product, [])
        assert len(mappings) == 0
    
    def test_zero_price_handling(self, agent):
        """Test handling of zero prices"""
        product_id = uuid4()
        historical_prices = [
            {
                'product_id': product_id,
                'price': Decimal("0.00"),
                'timestamp': datetime.utcnow() - timedelta(days=7)
            },
            {
                'product_id': product_id,
                'price': Decimal("100.00"),
                'timestamp': datetime.utcnow()
            }
        ]
        
        # Should not crash, should skip zero price records
        alerts = agent.detect_price_changes(historical_prices)
        assert isinstance(alerts, list)
    
    def test_missing_product_in_mapping(self, agent, sample_product, competitor_products):
        """Test handling of missing products in mappings"""
        # Create mapping with non-existent product ID
        mappings = [
            ProductEquivalenceMapping(
                our_product_id=uuid4(),  # Non-existent
                competitor_product_id=competitor_products[0].id,
                confidence=1.0,
                mapping_type="exact_sku"
            )
        ]
        
        price_gaps = agent.calculate_price_gaps(
            [sample_product],
            competitor_products,
            mappings
        )
        
        # Should handle gracefully and return empty list
        assert len(price_gaps) == 0
