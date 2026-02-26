"""Integration tests for Tiered Confidence Pipeline"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal

from src.agents.data_qa_agent import DataQAAgent
from src.agents.pricing_intelligence_v2 import EnhancedPricingIntelligenceAgent
from src.agents.sentiment_analysis_v2 import EnhancedSentimentAgent
from src.schemas.product import ProductResponse
from src.schemas.review import ReviewResponse
from src.schemas.pricing import MarginConstraints, MarketData


class TestTieredConfidencePipeline:
    """Test suite for tiered confidence calculation"""
    
    @pytest.fixture
    def qa_agent(self):
        """Create QA agent"""
        tenant_id = uuid4()
        return DataQAAgent(tenant_id=tenant_id)
    
    @pytest.fixture
    def pricing_agent(self):
        """Create enhanced pricing agent"""
        tenant_id = uuid4()
        return EnhancedPricingIntelligenceAgent(tenant_id=tenant_id)
    
    @pytest.fixture
    def sentiment_agent(self):
        """Create enhanced sentiment agent"""
        tenant_id = uuid4()
        return EnhancedSentimentAgent(tenant_id=tenant_id)
    
    @pytest.fixture
    def high_quality_products(self):
        """Create high-quality product data"""
        return [
            ProductResponse(
                id=uuid4(),
                sku="HQ-PROD-001",
                normalized_sku="HQPROD001",
                name="High Quality Product 1",
                category="Electronics",
                price=Decimal("99.99"),
                currency="USD",
                marketplace="test",
                inventory_level=50,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            ProductResponse(
                id=uuid4(),
                sku="HQ-PROD-002",
                normalized_sku="HQPROD002",
                name="High Quality Product 2",
                category="Electronics",
                price=Decimal("149.99"),
                currency="USD",
                marketplace="test",
                inventory_level=30,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
    
    @pytest.fixture
    def low_quality_products(self):
        """Create low-quality product data with issues"""
        return [
            ProductResponse(
                id=uuid4(),
                sku="LQ-001",
                normalized_sku="LQ001",
                name="Low Quality Product",
                category=None,  # Missing category
                price=Decimal("9999.99"),  # Outlier price
                currency="USD",
                marketplace="test",
                inventory_level=None,  # Missing inventory
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow() - timedelta(days=60)  # Stale data
            )
        ]
    
    @pytest.fixture
    def high_quality_reviews(self):
        """Create high-quality review data"""
        product_id = uuid4()
        return [
            ReviewResponse(
                id=uuid4(),
                product_id=product_id,
                rating=5,
                text="Excellent product! Highly recommend. Great value for money.",
                sentiment="positive",
                sentiment_confidence=0.95,
                is_spam=False,
                created_at=datetime.utcnow(),
                source="test"
            ),
            ReviewResponse(
                id=uuid4(),
                product_id=product_id,
                rating=4,
                text="Good quality, but could use some improvements.",
                sentiment="positive",
                sentiment_confidence=0.80,
                is_spam=False,
                created_at=datetime.utcnow(),
                source="test"
            ),
            ReviewResponse(
                id=uuid4(),
                product_id=product_id,
                rating=3,
                text="It's okay, nothing special.",
                sentiment="neutral",
                sentiment_confidence=0.70,
                is_spam=False,
                created_at=datetime.utcnow(),
                source="test"
            )
        ]
    
    @pytest.fixture
    def low_quality_reviews(self):
        """Create low-quality review data with issues"""
        product_id = uuid4()
        reviews = []
        
        # Create review surge (many reviews in short time)
        for i in range(15):
            reviews.append(ReviewResponse(
                id=uuid4(),
                product_id=product_id,
                rating=5 if i < 10 else 1,  # Polarized ratings
                text=f"Review {i}",  # Short, low-quality text
                sentiment="positive" if i < 10 else "negative",
                sentiment_confidence=0.60,
                is_spam=i % 5 == 0,  # Some spam
                created_at=datetime.utcnow() - timedelta(days=i % 3),  # All recent
                source="test"
            ))
        
        return reviews
    
    # ==================== Pricing Agent Tests ====================
    
    def test_pricing_confidence_with_high_quality_data(
        self,
        qa_agent,
        pricing_agent,
        high_quality_products
    ):
        """Test pricing confidence with high-quality data"""
        # Assess data quality
        qa_report = qa_agent.assess_product_data_quality(high_quality_products)
        
        # Quality should be high
        assert qa_report.overall_quality_score > 0.8
        
        # Calculate confidence
        base_confidence = 0.85
        confidence_data = pricing_agent.calculate_confidence_with_qa(
            base_confidence,
            qa_report,
            high_quality_products[0].id
        )
        
        # Final confidence should be close to base (minimal penalty)
        assert confidence_data['final_confidence'] > 0.70
        assert confidence_data['data_quality_score'] > 0.8
        assert confidence_data['anomaly_penalty'] == 1.0  # No anomalies
        
        # Explanation should be positive
        assert "Base analysis confidence" in confidence_data['explanation']
        
        print(f"\n✅ High Quality Data:")
        print(f"   Base Confidence: {confidence_data['base_confidence']:.1%}")
        print(f"   QA Score: {confidence_data['data_quality_score']:.1%}")
        print(f"   Anomaly Penalty: {confidence_data['anomaly_penalty']:.1%}")
        print(f"   Final Confidence: {confidence_data['final_confidence']:.1%}")
        print(f"   Explanation: {confidence_data['explanation']}")
    
    def test_pricing_confidence_with_low_quality_data(
        self,
        qa_agent,
        pricing_agent,
        low_quality_products
    ):
        """Test pricing confidence with low-quality data"""
        # Assess data quality
        qa_report = qa_agent.assess_product_data_quality(low_quality_products)
        
        # Quality should be low
        assert qa_report.overall_quality_score < 0.7
        assert len(qa_report.anomalies) > 0
        
        # Calculate confidence
        base_confidence = 0.85
        confidence_data = pricing_agent.calculate_confidence_with_qa(
            base_confidence,
            qa_report,
            low_quality_products[0].id
        )
        
        # Final confidence should be significantly reduced
        assert confidence_data['final_confidence'] < base_confidence * 0.8
        assert confidence_data['data_quality_score'] < 0.7
        assert confidence_data['anomaly_penalty'] < 1.0  # Anomalies detected
        
        # Explanation should mention issues
        assert "reduced confidence" in confidence_data['explanation'].lower()
        
        print(f"\n⚠️  Low Quality Data:")
        print(f"   Base Confidence: {confidence_data['base_confidence']:.1%}")
        print(f"   QA Score: {confidence_data['data_quality_score']:.1%}")
        print(f"   Anomaly Penalty: {confidence_data['anomaly_penalty']:.1%}")
        print(f"   Final Confidence: {confidence_data['final_confidence']:.1%}")
        print(f"   Explanation: {confidence_data['explanation']}")
    
    def test_pricing_recommendation_with_qa(
        self,
        qa_agent,
        pricing_agent,
        high_quality_products
    ):
        """Test full pricing recommendation with QA integration"""
        # Assess data quality
        qa_report = qa_agent.assess_product_data_quality(high_quality_products)
        
        # Create market data
        market_data = MarketData(
            competitor_count=5,
            average_competitor_price=Decimal("110.00"),
            min_competitor_price=Decimal("95.00"),
            max_competitor_price=Decimal("125.00")
        )
        
        # Generate recommendation
        recommendation = pricing_agent.suggest_dynamic_pricing_with_qa(
            high_quality_products[0],
            market_data,
            MarginConstraints(min_margin_percentage=20.0, max_discount_percentage=30.0),
            qa_report
        )
        
        # Check recommendation structure
        assert recommendation.product_id == high_quality_products[0].id
        assert recommendation.confidence_score > 0
        assert recommendation.qa_metadata is not None
        
        # Check QA metadata
        qa_meta = recommendation.qa_metadata
        assert 'base_confidence' in qa_meta
        assert 'data_quality_score' in qa_meta
        assert 'anomaly_penalty' in qa_meta
        assert 'confidence_explanation' in qa_meta
        assert 'quality_dimensions' in qa_meta
        
        print(f"\n📊 Pricing Recommendation:")
        print(f"   Current Price: ${recommendation.current_price}")
        print(f"   Suggested Price: ${recommendation.suggested_price}")
        print(f"   Action: {recommendation.action}")
        print(f"   Final Confidence: {recommendation.confidence_score:.1%}")
        print(f"   QA Explanation: {qa_meta['confidence_explanation']}")
    
    # ==================== Sentiment Agent Tests ====================
    
    def test_sentiment_confidence_with_high_quality_reviews(
        self,
        qa_agent,
        sentiment_agent,
        high_quality_reviews
    ):
        """Test sentiment confidence with high-quality reviews"""
        # Assess review quality
        qa_report = qa_agent.assess_review_data_quality(high_quality_reviews)
        
        # Quality should be high
        assert qa_report.overall_quality_score > 0.7
        
        # Calculate confidence
        base_confidence = 0.75
        confidence_data = sentiment_agent.calculate_confidence_with_qa(
            base_confidence,
            qa_report,
            high_quality_reviews[0].product_id
        )
        
        # Final confidence should be close to base
        assert confidence_data['final_confidence'] > 0.60
        assert confidence_data['anomaly_penalty'] == 1.0  # No anomalies
        
        print(f"\n✅ High Quality Reviews:")
        print(f"   Base Confidence: {confidence_data['base_confidence']:.1%}")
        print(f"   QA Score: {confidence_data['data_quality_score']:.1%}")
        print(f"   Anomaly Penalty: {confidence_data['anomaly_penalty']:.1%}")
        print(f"   Final Confidence: {confidence_data['final_confidence']:.1%}")
    
    def test_sentiment_confidence_with_low_quality_reviews(
        self,
        qa_agent,
        sentiment_agent,
        low_quality_reviews
    ):
        """Test sentiment confidence with low-quality reviews"""
        # Assess review quality
        qa_report = qa_agent.assess_review_data_quality(low_quality_reviews)
        
        # Quality should be lower due to spam and anomalies
        assert len(qa_report.anomalies) > 0  # Should detect review surge or polarization
        
        # Calculate confidence
        base_confidence = 0.75
        confidence_data = sentiment_agent.calculate_confidence_with_qa(
            base_confidence,
            qa_report,
            low_quality_reviews[0].product_id
        )
        
        # Final confidence should be reduced
        assert confidence_data['final_confidence'] < base_confidence
        
        # Should have anomaly penalty
        if qa_report.anomalies:
            assert confidence_data['anomaly_penalty'] < 1.0
        
        print(f"\n⚠️  Low Quality Reviews:")
        print(f"   Base Confidence: {confidence_data['base_confidence']:.1%}")
        print(f"   QA Score: {confidence_data['data_quality_score']:.1%}")
        print(f"   Anomaly Penalty: {confidence_data['anomaly_penalty']:.1%}")
        print(f"   Final Confidence: {confidence_data['final_confidence']:.1%}")
        print(f"   Anomalies Detected: {len(qa_report.anomalies)}")
    
    def test_sentiment_analysis_with_qa(
        self,
        qa_agent,
        sentiment_agent,
        high_quality_reviews
    ):
        """Test full sentiment analysis with QA integration"""
        # Assess review quality
        qa_report = qa_agent.assess_review_data_quality(high_quality_reviews)
        
        # Perform sentiment analysis
        result = sentiment_agent.calculate_aggregate_sentiment_with_qa(
            high_quality_reviews,
            qa_report
        )
        
        # Check result structure
        assert result.product_id == high_quality_reviews[0].product_id
        assert result.confidence_score > 0
        assert result.qa_metadata is not None
        
        # Check QA metadata
        qa_meta = result.qa_metadata
        assert 'base_confidence' in qa_meta
        assert 'data_quality_score' in qa_meta
        assert 'anomaly_penalty' in qa_meta
        assert 'confidence_explanation' in qa_meta
        
        print(f"\n📊 Sentiment Analysis:")
        print(f"   Aggregate Sentiment: {result.aggregate_sentiment:.2f}")
        print(f"   Total Reviews: {result.total_reviews}")
        print(f"   Final Confidence: {result.confidence_score:.1%}")
        print(f"   QA Explanation: {qa_meta['confidence_explanation']}")
    
    # ==================== Confidence Formula Tests ====================
    
    def test_confidence_formula_components(self, qa_agent, pricing_agent):
        """Test that confidence formula is correctly applied"""
        # Create test data with known quality
        products = [
            ProductResponse(
                id=uuid4(),
                sku="TEST-001",
                normalized_sku="TEST001",
                name="Test Product",
                category="Electronics",
                price=Decimal("100.00"),
                currency="USD",
                marketplace="test",
                inventory_level=10,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        qa_report = qa_agent.assess_product_data_quality(products)
        
        # Test with known values
        base_confidence = 0.80
        confidence_data = pricing_agent.calculate_confidence_with_qa(
            base_confidence,
            qa_report,
            products[0].id
        )
        
        # Verify formula: final = base × qa_score × anomaly_penalty
        expected = (
            confidence_data['base_confidence'] *
            confidence_data['data_quality_score'] *
            confidence_data['anomaly_penalty']
        )
        
        assert abs(confidence_data['final_confidence'] - expected) < 0.001
        
        print(f"\n🧮 Confidence Formula Verification:")
        print(f"   Formula: final = base × qa_score × anomaly_penalty")
        print(f"   Base: {confidence_data['base_confidence']:.3f}")
        print(f"   QA Score: {confidence_data['data_quality_score']:.3f}")
        print(f"   Anomaly Penalty: {confidence_data['anomaly_penalty']:.3f}")
        print(f"   Expected: {expected:.3f}")
        print(f"   Actual: {confidence_data['final_confidence']:.3f}")
        print(f"   ✓ Formula correctly applied!")
    
    def test_anomaly_severity_penalties(self, qa_agent, pricing_agent):
        """Test that different anomaly severities apply correct penalties"""
        from src.schemas.data_quality import Anomaly, DataQualityReport, DataQualityDimensions, QualityDimension
        
        # Create reports with different severity anomalies
        severities = ['low', 'medium', 'high', 'critical']
        expected_penalties = [0.95, 0.85, 0.70, 0.50]
        
        for severity, expected_penalty in zip(severities, expected_penalties):
            # Create QA report with specific severity anomaly
            empty_dim = QualityDimension(score=1.0, issues_count=0)
            qa_report = DataQualityReport(
                overall_quality_score=1.0,
                dimensions=DataQualityDimensions(
                    completeness=empty_dim,
                    validity=empty_dim,
                    freshness=empty_dim,
                    consistency=empty_dim,
                    accuracy=empty_dim
                ),
                anomalies=[
                    Anomaly(
                        type="test_anomaly",
                        severity=severity,
                        description=f"Test {severity} anomaly",
                        affected_entities=["test-id"],
                        confidence=0.9
                    )
                ],
                missing_data=[],
                recommendations=[],
                entities_assessed=1,
                assessment_timestamp=datetime.utcnow().isoformat()
            )
            
            # Calculate confidence
            confidence_data = pricing_agent.calculate_confidence_with_qa(
                1.0,  # Base confidence
                qa_report
            )
            
            # Verify penalty
            assert confidence_data['anomaly_penalty'] == expected_penalty
            
            print(f"\n   {severity.upper()}: penalty = {expected_penalty:.2f} ✓")
    
    # ==================== Integration Test ====================
    
    def test_end_to_end_tiered_pipeline(
        self,
        qa_agent,
        pricing_agent,
        sentiment_agent,
        high_quality_products,
        high_quality_reviews
    ):
        """Test complete end-to-end tiered intelligence pipeline"""
        print(f"\n{'='*60}")
        print("END-TO-END TIERED INTELLIGENCE PIPELINE TEST")
        print(f"{'='*60}")
        
        # Layer 0: Data QA Assessment
        print(f"\n📋 LAYER 0: Data Quality Assessment")
        product_qa = qa_agent.assess_product_data_quality(high_quality_products)
        review_qa = qa_agent.assess_review_data_quality(high_quality_reviews)
        
        print(f"   Product Quality: {product_qa.overall_quality_score:.1%}")
        print(f"   Review Quality: {review_qa.overall_quality_score:.1%}")
        print(f"   Anomalies: {len(product_qa.anomalies) + len(review_qa.anomalies)}")
        
        # Layer 1: Domain Intelligence Agents
        print(f"\n🤖 LAYER 1: Domain Intelligence Agents")
        
        # Pricing analysis
        market_data = MarketData(
            competitor_count=5,
            average_competitor_price=Decimal("110.00"),
            min_competitor_price=Decimal("95.00"),
            max_competitor_price=Decimal("125.00")
        )
        
        pricing_rec = pricing_agent.suggest_dynamic_pricing_with_qa(
            high_quality_products[0],
            market_data,
            MarginConstraints(min_margin_percentage=20.0, max_discount_percentage=30.0),
            product_qa
        )
        
        print(f"   Pricing Agent:")
        print(f"      Recommendation: {pricing_rec.action} price to ${pricing_rec.suggested_price}")
        print(f"      Confidence: {pricing_rec.confidence_score:.1%}")
        
        # Sentiment analysis
        sentiment_result = sentiment_agent.calculate_aggregate_sentiment_with_qa(
            high_quality_reviews,
            review_qa
        )
        
        print(f"   Sentiment Agent:")
        print(f"      Aggregate Sentiment: {sentiment_result.aggregate_sentiment:.2f}")
        print(f"      Confidence: {sentiment_result.confidence_score:.1%}")
        
        # Layer 2: Synthesis (simulated)
        print(f"\n🎯 LAYER 2: Synthesis & Orchestration")
        overall_confidence = (pricing_rec.confidence_score + sentiment_result.confidence_score) / 2
        print(f"   Overall Confidence: {overall_confidence:.1%}")
        print(f"   Data Quality Impact: Visible in all agent outputs")
        print(f"   Transparency: Full QA metadata available")
        
        # Verify QA metadata is present
        assert pricing_rec.qa_metadata is not None
        assert sentiment_result.qa_metadata is not None
        
        print(f"\n✅ Pipeline Complete - All layers functioning correctly!")
        print(f"{'='*60}\n")
