"""Tests for Data QA Agent"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.agents.data_qa_agent import DataQAAgent
from src.schemas.product import ProductResponse
from src.schemas.review import ReviewResponse


class TestDataQAAgent:
    """Test suite for Data QA Agent"""
    
    @pytest.fixture
    def qa_agent(self):
        """Create QA agent instance"""
        tenant_id = uuid4()
        return DataQAAgent(tenant_id=tenant_id)
    
    @pytest.fixture
    def valid_products(self):
        """Create valid product data"""
        return [
            ProductResponse(
                id=uuid4(),
                sku="PROD-001",
                normalized_sku="PROD001",
                name="Test Product 1",
                category="Electronics",
                price=99.99,
                currency="USD",
                marketplace="test",
                inventory_level=50,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            ProductResponse(
                id=uuid4(),
                sku="PROD-002",
                normalized_sku="PROD002",
                name="Test Product 2",
                category="Electronics",
                price=149.99,
                currency="USD",
                marketplace="test",
                inventory_level=30,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            ProductResponse(
                id=uuid4(),
                sku="PROD-003",
                normalized_sku="PROD003",
                name="Test Product 3",
                category="Electronics",
                price=199.99,
                currency="USD",
                marketplace="test",
                inventory_level=20,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
    
    @pytest.fixture
    def valid_reviews(self):
        """Create valid review data"""
        product_id = uuid4()
        return [
            ReviewResponse(
                id=uuid4(),
                product_id=product_id,
                rating=5,
                text="Excellent product! Highly recommend.",
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
                text="Good quality, but a bit expensive.",
                sentiment="positive",
                sentiment_confidence=0.75,
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
                sentiment_confidence=0.60,
                is_spam=False,
                created_at=datetime.utcnow(),
                source="test"
            )
        ]
    
    # ==================== Product Quality Tests ====================
    
    def test_assess_valid_product_data(self, qa_agent, valid_products):
        """Test assessment of valid product data"""
        report = qa_agent.assess_product_data_quality(valid_products)
        
        assert report.overall_quality_score > 0.8
        assert report.entities_assessed == 3
        assert report.dimensions.completeness.score > 0.8
        assert report.dimensions.validity.score == 1.0
        assert len(report.anomalies) == 0
    
    def test_detect_price_outliers(self, qa_agent, valid_products):
        """Test detection of price outliers"""
        # Add a product with outlier price
        outlier_product = ProductResponse(
            id=uuid4(),
            sku="OUTLIER-001",
            normalized_sku="OUTLIER001",
            name="Outlier Product",
            category="Electronics",
            price=9999.99,  # Way higher than others
            currency="USD",
            marketplace="test",
            inventory_level=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        products = valid_products + [outlier_product]
        report = qa_agent.assess_product_data_quality(products)
        
        # Should detect price outlier
        price_anomalies = [a for a in report.anomalies if a.type == "price_outlier"]
        assert len(price_anomalies) > 0
        assert str(outlier_product.id) in price_anomalies[0].affected_entities
    
    def test_detect_stale_data(self, qa_agent, valid_products):
        """Test detection of stale data"""
        # Make one product stale
        stale_product = valid_products[0]
        stale_product.updated_at = datetime.utcnow() - timedelta(days=60)
        
        report = qa_agent.assess_product_data_quality(valid_products)
        
        # Freshness score should be reduced
        assert report.dimensions.freshness.score < 1.0
        assert report.dimensions.freshness.issues_count > 0
    
    def test_detect_missing_product_data(self, qa_agent):
        """Test detection of missing product data"""
        incomplete_products = [
            ProductResponse(
                id=uuid4(),
                sku="INCOMPLETE-001",
                normalized_sku="INCOMPLETE001",
                name="Incomplete Product",
                category=None,  # Missing category
                price=99.99,
                currency="USD",
                marketplace="test",
                inventory_level=None,  # Missing inventory
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        report = qa_agent.assess_product_data_quality(incomplete_products)
        
        # Should identify missing data
        assert len(report.missing_data) > 0
        missing_fields = [m.field for m in report.missing_data]
        assert "category" in missing_fields or "inventory_level" in missing_fields
    
    def test_detect_invalid_product_data(self, qa_agent):
        """Test detection of invalid product data"""
        invalid_products = [
            ProductResponse(
                id=uuid4(),
                sku="INV",  # Too short
                normalized_sku="INV",
                name="Invalid Product",
                category="Electronics",
                price=-10.00,  # Negative price
                currency="US",  # Invalid currency code
                marketplace="test",
                inventory_level=-5,  # Negative inventory
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        report = qa_agent.assess_product_data_quality(invalid_products)
        
        # Validity score should be low
        assert report.dimensions.validity.score < 0.5
        assert report.dimensions.validity.issues_count > 0
    
    def test_detect_duplicate_skus(self, qa_agent, valid_products):
        """Test detection of duplicate SKUs"""
        # Add duplicate SKU
        duplicate_product = ProductResponse(
            id=uuid4(),
            sku="PROD-001",  # Duplicate
            normalized_sku="PROD001",
            name="Duplicate Product",
            category="Electronics",
            price=99.99,
            currency="USD",
            marketplace="test",
            inventory_level=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        products = valid_products + [duplicate_product]
        report = qa_agent.assess_product_data_quality(products)
        
        # Consistency score should be reduced
        assert report.dimensions.consistency.score < 1.0
        assert report.dimensions.consistency.issues_count > 0
    
    def test_detect_high_out_of_stock_rate(self, qa_agent):
        """Test detection of high out-of-stock rate"""
        products = []
        for i in range(10):
            products.append(ProductResponse(
                id=uuid4(),
                sku=f"PROD-{i:03d}",
                normalized_sku=f"PROD{i:03d}",
                name=f"Product {i}",
                category="Electronics",
                price=99.99,
                currency="USD",
                marketplace="test",
                inventory_level=0 if i < 7 else 10,  # 70% out of stock
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ))
        
        report = qa_agent.assess_product_data_quality(products)
        
        # Should detect high out-of-stock rate
        oos_anomalies = [a for a in report.anomalies if a.type == "high_out_of_stock_rate"]
        assert len(oos_anomalies) > 0
    
    def test_product_quality_metadata(self, qa_agent, valid_products):
        """Test generation of product-specific quality metadata"""
        report = qa_agent.assess_product_data_quality(valid_products)
        metadata = qa_agent.get_product_quality_metadata(valid_products[0], report)
        
        assert metadata.product_id == valid_products[0].id
        assert 0.0 <= metadata.quality_score <= 1.0
        assert isinstance(metadata.issues, list)
        assert isinstance(metadata.warnings, list)
    
    # ==================== Review Quality Tests ====================
    
    def test_assess_valid_review_data(self, qa_agent, valid_reviews):
        """Test assessment of valid review data"""
        report = qa_agent.assess_review_data_quality(valid_reviews)
        
        assert report.overall_quality_score > 0.7
        assert report.entities_assessed == 3
        assert report.dimensions.completeness.score > 0.8
        assert report.dimensions.validity.score == 1.0
    
    def test_detect_spam_reviews(self, qa_agent, valid_reviews):
        """Test detection of spam reviews"""
        spam_review = ReviewResponse(
            id=uuid4(),
            product_id=valid_reviews[0].product_id,
            rating=5,
            text="BUY NOW!!! AMAZING DEAL!!! CLICK HERE!!!",
            sentiment="positive",
            sentiment_confidence=0.5,
            is_spam=True,
            created_at=datetime.utcnow(),
            source="test"
        )
        
        reviews = valid_reviews + [spam_review]
        report = qa_agent.assess_review_data_quality(reviews)
        
        # Accuracy score should be reduced
        assert report.dimensions.accuracy.score < 1.0
        assert report.dimensions.accuracy.issues_count > 0
    
    def test_detect_rating_text_mismatch(self, qa_agent):
        """Test detection of rating-text mismatches"""
        mismatched_reviews = [
            ReviewResponse(
                id=uuid4(),
                product_id=uuid4(),
                rating=5,  # High rating
                text="This is terrible! Worst product ever!",  # Negative text
                sentiment="negative",
                sentiment_confidence=0.9,
                is_spam=False,
                created_at=datetime.utcnow(),
                source="test"
            ),
            ReviewResponse(
                id=uuid4(),
                product_id=uuid4(),
                rating=1,  # Low rating
                text="Amazing product! Love it!",  # Positive text
                sentiment="positive",
                sentiment_confidence=0.9,
                is_spam=False,
                created_at=datetime.utcnow(),
                source="test"
            )
        ]
        
        report = qa_agent.assess_review_data_quality(mismatched_reviews)
        
        # Consistency score should be low
        assert report.dimensions.consistency.score < 1.0
        assert report.dimensions.consistency.issues_count >= 2
    
    def test_detect_review_surge(self, qa_agent):
        """Test detection of review surge (possible review bombing)"""
        product_id = uuid4()
        reviews = []
        
        # Create many recent reviews
        for i in range(15):
            reviews.append(ReviewResponse(
                id=uuid4(),
                product_id=product_id,
                rating=1,
                text=f"Bad product {i}",
                sentiment="negative",
                sentiment_confidence=0.8,
                is_spam=False,
                created_at=datetime.utcnow() - timedelta(days=i % 3),  # All within 3 days
                source="test"
            ))
        
        report = qa_agent.assess_review_data_quality(reviews)
        
        # Should detect review surge
        surge_anomalies = [a for a in report.anomalies if a.type == "review_surge"]
        assert len(surge_anomalies) > 0
    
    def test_detect_rating_polarization(self, qa_agent):
        """Test detection of rating polarization"""
        product_id = uuid4()
        reviews = []
        
        # Create polarized ratings (mostly 1s and 5s)
        for i in range(10):
            rating = 1 if i < 5 else 5
            reviews.append(ReviewResponse(
                id=uuid4(),
                product_id=product_id,
                rating=rating,
                text=f"Review {i}",
                sentiment="positive" if rating == 5 else "negative",
                sentiment_confidence=0.8,
                is_spam=False,
                created_at=datetime.utcnow(),
                source="test"
            ))
        
        report = qa_agent.assess_review_data_quality(reviews)
        
        # Should detect polarization
        polar_anomalies = [a for a in report.anomalies if a.type == "rating_polarization"]
        assert len(polar_anomalies) > 0
    
    def test_detect_old_reviews(self, qa_agent):
        """Test detection of old reviews"""
        old_reviews = [
            ReviewResponse(
                id=uuid4(),
                product_id=uuid4(),
                rating=4,
                text="Good product",
                sentiment="positive",
                sentiment_confidence=0.8,
                is_spam=False,
                created_at=datetime.utcnow() - timedelta(days=120),  # 4 months old
                source="test"
            )
        ]
        
        report = qa_agent.assess_review_data_quality(old_reviews)
        
        # Freshness score should be reduced
        assert report.dimensions.freshness.score < 1.0
        assert report.dimensions.freshness.issues_count > 0
    
    def test_detect_invalid_reviews(self, qa_agent):
        """Test detection of invalid reviews"""
        invalid_reviews = [
            ReviewResponse(
                id=uuid4(),
                product_id=uuid4(),
                rating=10,  # Invalid rating
                text="OK",  # Too short
                sentiment="positive",
                sentiment_confidence=0.5,
                is_spam=False,
                created_at=datetime.utcnow(),
                source="test"
            )
        ]
        
        report = qa_agent.assess_review_data_quality(invalid_reviews)
        
        # Validity score should be low
        assert report.dimensions.validity.score < 1.0
        assert report.dimensions.validity.issues_count > 0
    
    # ==================== Edge Cases ====================
    
    def test_empty_product_list(self, qa_agent):
        """Test handling of empty product list"""
        report = qa_agent.assess_product_data_quality([])
        
        assert report.overall_quality_score == 0.0
        assert report.entities_assessed == 0
        assert len(report.recommendations) > 0
    
    def test_empty_review_list(self, qa_agent):
        """Test handling of empty review list"""
        report = qa_agent.assess_review_data_quality([])
        
        assert report.overall_quality_score == 0.0
        assert report.entities_assessed == 0
        assert len(report.recommendations) > 0
    
    def test_single_product(self, qa_agent, valid_products):
        """Test assessment with single product"""
        report = qa_agent.assess_product_data_quality([valid_products[0]])
        
        assert report.entities_assessed == 1
        assert report.overall_quality_score > 0.0
        # Should not detect outliers with single product
        assert len([a for a in report.anomalies if a.type == "price_outlier"]) == 0
    
    def test_recommendations_generation(self, qa_agent, valid_products):
        """Test that recommendations are generated"""
        # Make data problematic
        valid_products[0].updated_at = datetime.utcnow() - timedelta(days=60)
        valid_products[1].category = None
        
        report = qa_agent.assess_product_data_quality(valid_products)
        
        assert len(report.recommendations) > 0
        assert any("refresh" in r.lower() or "add" in r.lower() for r in report.recommendations)
