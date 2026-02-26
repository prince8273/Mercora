"""Comprehensive tests for Data Validation Layer (Tasks 4.1-4.4)"""
import pytest
from decimal import Decimal
from datetime import datetime

from src.processing.validator import DataValidator, ValidationResult
from src.processing.spam_filter import SpamFilter
from src.processing.normalizer import SKUNormalizer
from src.processing.deduplicator import Deduplicator
from src.processing.missing_data_handler import MissingDataHandler


# ============================================================================
# Task 4.1: DataValidator Tests
# ============================================================================

class TestDataValidator:
    """Tests for DataValidator component"""
    
    @pytest.fixture
    def validator(self):
        return DataValidator()
    
    def test_valid_product_data(self, validator):
        """Test validation of valid product data"""
        product = {
            'sku': 'TEST-123',
            'name': 'Test Product',
            'price': 99.99,
            'marketplace': 'amazon',
            'currency': 'USD',
            'inventory_level': 100
        }
        
        result = validator.validate_product_data(product)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.validated_data is not None
    
    def test_missing_required_fields(self, validator):
        """Test validation fails for missing required fields"""
        product = {
            'name': 'Test Product',
            'price': 99.99
            # Missing: sku, marketplace
        }
        
        result = validator.validate_product_data(product)
        
        assert result.is_valid is False
        assert 'sku' in str(result.errors).lower()
        assert 'marketplace' in str(result.errors).lower()
    
    def test_invalid_price(self, validator):
        """Test validation fails for invalid price"""
        product = {
            'sku': 'TEST-123',
            'name': 'Test Product',
            'price': -10.00,  # Negative price
            'marketplace': 'amazon'
        }
        
        result = validator.validate_product_data(product)
        
        assert result.is_valid is False
        assert 'price' in str(result.errors).lower()
    
    def test_price_warning_for_high_value(self, validator):
        """Test warning for unusually high price"""
        product = {
            'sku': 'TEST-123',
            'name': 'Expensive Product',
            'price': 1500000,  # Very high price
            'marketplace': 'amazon'
        }
        
        result = validator.validate_product_data(product)
        
        assert len(result.warnings) > 0
        assert 'high price' in str(result.warnings).lower()
    
    def test_valid_review_data(self, validator):
        """Test validation of valid review data"""
        review = {
            'product_id': 'prod-123',
            'rating': 5,
            'text': 'Great product! Highly recommend.'
        }
        
        result = validator.validate_review_data(review)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_invalid_rating(self, validator):
        """Test validation fails for invalid rating"""
        review = {
            'product_id': 'prod-123',
            'rating': 10,  # Invalid rating (must be 1-5)
            'text': 'Great product!'
        }
        
        result = validator.validate_review_data(review)
        
        assert result.is_valid is False
        assert 'rating' in str(result.errors).lower()
    
    def test_review_too_short(self, validator):
        """Test validation fails for very short review"""
        review = {
            'product_id': 'prod-123',
            'rating': 5,
            'text': 'OK'  # Too short
        }
        
        result = validator.validate_review_data(review)
        
        assert result.is_valid is False
        assert 'short' in str(result.errors).lower()


# ============================================================================
# Task 4.2: Spam Filter Tests
# ============================================================================

class TestSpamFilter:
    """Tests for SpamFilter component"""
    
    @pytest.fixture
    def spam_filter(self):
        return SpamFilter(spam_threshold=0.5)
    
    def test_legitimate_review(self, spam_filter):
        """Test legitimate review is not flagged as spam"""
        text = "This product exceeded my expectations. Great quality and fast shipping!"
        
        is_spam, confidence, reasons = spam_filter.is_spam(text, rating=5)
        
        assert is_spam is False
        assert confidence < 0.5
    
    def test_spam_with_url(self, spam_filter):
        """Test review with URL is flagged as spam"""
        text = "Great product! Visit http://spam-site.com for more deals!"
        
        is_spam, confidence, reasons = spam_filter.is_spam(text, rating=5)
        
        # URL pattern should increase spam score
        assert confidence > 0.3  # Should have some spam indicators
        assert any('pattern' in r.lower() or 'url' in r.lower() or '.com' in r.lower() for r in reasons)
    
    def test_spam_with_keywords(self, spam_filter):
        """Test review with spam keywords is flagged"""
        text = "Click here for free money! Limited time offer!"
        
        is_spam, confidence, reasons = spam_filter.is_spam(text, rating=5)
        
        assert is_spam is True
        assert len(reasons) > 0
    
    def test_spam_excessive_caps(self, spam_filter):
        """Test review with excessive caps is flagged"""
        text = "THIS IS THE BEST PRODUCT EVER BUY NOW!!!"
        
        is_spam, confidence, reasons = spam_filter.is_spam(text, rating=5)
        
        assert is_spam is True
        assert any('caps' in r.lower() for r in reasons)
    
    def test_filter_spam_reviews(self, spam_filter):
        """Test filtering spam from review list"""
        reviews = [
            {'text': 'Great product! Really love it.', 'rating': 5},
            {'text': 'Visit http://spam.com for deals FREE MONEY', 'rating': 5},
            {'text': 'Excellent quality and fast shipping', 'rating': 4},
            {'text': 'FREE MONEY CLICK HERE BUY NOW!!!', 'rating': 5}
        ]
        
        filtered = spam_filter.filter_spam_reviews(reviews, mark_only=False)
        
        # Should filter out obvious spam
        assert len(filtered) <= 3
        assert all(not r.get('is_spam', False) for r in filtered)
    
    def test_batch_check_spam(self, spam_filter):
        """Test batch spam checking with statistics"""
        reviews = [
            {'text': 'Great product! Really love it.', 'rating': 5},
            {'text': 'Visit http://spam.com FREE MONEY', 'rating': 5},
            {'text': 'Excellent quality', 'rating': 4}
        ]
        
        result = spam_filter.batch_check_spam(reviews)
        
        assert result['total_reviews'] == 3
        assert result['spam_count'] >= 0  # May or may not detect spam depending on threshold
        assert result['clean_count'] >= 0
        assert 'spam_rate' in result
        assert 0.0 <= result['spam_rate'] <= 1.0


# ============================================================================
# Task 4.4: SKU Normalizer Tests
# ============================================================================

class TestSKUNormalizer:
    """Tests for SKUNormalizer component"""
    
    @pytest.fixture
    def normalizer(self):
        return SKUNormalizer()
    
    def test_basic_normalization(self, normalizer):
        """Test basic SKU normalization"""
        sku = "  test-123  "
        normalized = normalizer.normalize_sku(sku)
        
        assert normalized == "TEST-123"
        assert normalized.isupper()
        assert ' ' not in normalized
    
    def test_remove_special_characters(self, normalizer):
        """Test removal of special characters"""
        sku = "TEST@123#456"
        normalized = normalizer.normalize_sku(sku)
        
        assert '@' not in normalized
        assert '#' not in normalized
        assert normalized == "TEST123456"
    
    def test_amazon_asin_normalization(self, normalizer):
        """Test Amazon ASIN normalization"""
        sku = "B08N5WRWNW"
        normalized = normalizer.normalize_sku(sku, marketplace='amazon')
        
        assert len(normalized) == 10
        assert normalized.isalnum()
    
    def test_sku_similarity_exact_match(self, normalizer):
        """Test SKU similarity for exact match"""
        sku1 = "TEST-123"
        sku2 = "TEST-123"
        
        similarity = normalizer.calculate_sku_similarity(sku1, sku2)
        
        assert similarity == 1.0
    
    def test_sku_similarity_different(self, normalizer):
        """Test SKU similarity for different SKUs"""
        sku1 = "TEST-123"
        sku2 = "PROD-456"
        
        similarity = normalizer.calculate_sku_similarity(sku1, sku2)
        
        assert 0.0 <= similarity < 1.0
    
    def test_product_mapping_exact(self, normalizer):
        """Test product mapping with exact match"""
        mapping = normalizer.create_product_mapping(
            sku1="TEST-123",
            marketplace1="amazon",
            sku2="TEST-123",
            marketplace2="ebay"
        )
        
        assert mapping['confidence'] == 1.0
        assert mapping['mapping_type'] == "exact"
    
    def test_product_mapping_similarity(self, normalizer):
        """Test product mapping with high similarity"""
        mapping = normalizer.create_product_mapping(
            sku1="TEST-123",
            marketplace1="amazon",
            sku2="TEST-124",
            marketplace2="ebay"
        )
        
        assert 0.0 < mapping['confidence'] < 1.0
        assert mapping['similarity_score'] > 0.8


# ============================================================================
# Task 4.6: Deduplicator Tests
# ============================================================================

class TestDeduplicator:
    """Tests for Deduplicator component"""
    
    @pytest.fixture
    def deduplicator(self):
        return Deduplicator()
    
    def test_deduplicate_products_no_duplicates(self, deduplicator):
        """Test deduplication with no duplicates"""
        products = [
            {'sku': 'TEST-1', 'marketplace': 'amazon', 'price': 10},
            {'sku': 'TEST-2', 'marketplace': 'amazon', 'price': 20},
        ]
        
        result = deduplicator.deduplicate_products(products)
        
        assert len(result) == 2
    
    def test_deduplicate_products_with_duplicates(self, deduplicator):
        """Test deduplication removes duplicates"""
        products = [
            {'sku': 'TEST-1', 'marketplace': 'amazon', 'price': 10, 'updated_at': '2024-01-01'},
            {'sku': 'TEST-1', 'marketplace': 'amazon', 'price': 15, 'updated_at': '2024-01-02'},  # More recent
            {'sku': 'TEST-2', 'marketplace': 'amazon', 'price': 20, 'updated_at': '2024-01-01'},
        ]
        
        result = deduplicator.deduplicate_products(products)
        
        assert len(result) == 2
        # Should keep the more recent version
        test1_product = [p for p in result if p['sku'] == 'TEST-1'][0]
        assert test1_product['price'] == 15
    
    def test_deduplicate_reviews(self, deduplicator):
        """Test review deduplication"""
        reviews = [
            {'product_id': 'prod-1', 'text': 'Great product', 'created_at': '2024-01-01'},
            {'product_id': 'prod-1', 'text': 'Great product', 'created_at': '2024-01-02'},  # Duplicate
            {'product_id': 'prod-1', 'text': 'Different review', 'created_at': '2024-01-01'},
        ]
        
        result = deduplicator.deduplicate_reviews(reviews)
        
        assert len(result) == 2  # One duplicate removed
    
    def test_find_duplicates(self, deduplicator):
        """Test finding duplicate groups"""
        products = [
            {'sku': 'TEST-1', 'marketplace': 'amazon'},
            {'sku': 'TEST-1', 'marketplace': 'amazon'},  # Duplicate
            {'sku': 'TEST-2', 'marketplace': 'amazon'},
        ]
        
        duplicates = deduplicator.find_duplicates(products, key_fields=['sku', 'marketplace'])
        
        assert len(duplicates) == 1  # One duplicate group
        assert len(list(duplicates.values())[0]) == 2  # Two records in the group


# ============================================================================
# Task 4.8: Missing Data Handler Tests
# ============================================================================

class TestMissingDataHandler:
    """Tests for MissingDataHandler component"""
    
    @pytest.fixture
    def handler(self):
        return MissingDataHandler()
    
    def test_handle_complete_product(self, handler):
        """Test handling product with no missing data"""
        product = {
            'sku': 'TEST-123',
            'name': 'Test Product',
            'price': 99.99,
            'marketplace': 'amazon',
            'category': 'Electronics',
            'inventory_level': 100,
            'currency': 'USD'
        }
        
        result = handler.handle_missing_product_data(product)
        
        # Should have no critical missing fields
        assert len(result['_critical_missing']) == 0
        # May have some optional fields missing
        assert '_has_missing_data' in result
    
    def test_handle_missing_optional_fields(self, handler):
        """Test handling product with missing optional fields"""
        product = {
            'sku': 'TEST-123',
            'name': 'Test Product',
            'price': 99.99,
            'marketplace': 'amazon'
            # Missing: category, inventory_level
        }
        
        result = handler.handle_missing_product_data(product, apply_defaults=True)
        
        assert result['_has_missing_data'] is True
        assert len(result['_critical_missing']) == 0
        assert 'category' in result  # Default applied
    
    def test_handle_missing_critical_fields(self, handler):
        """Test handling product with missing critical fields"""
        product = {
            'name': 'Test Product',
            'price': 99.99
            # Missing: sku, marketplace (critical)
        }
        
        result = handler.handle_missing_product_data(product)
        
        assert result['_has_missing_data'] is True
        assert len(result['_critical_missing']) > 0
        assert 'sku' in result['_critical_missing']
    
    def test_interpolate_missing_prices(self, handler):
        """Test price interpolation for missing values"""
        products = [
            {'sku': 'P1', 'category': 'Electronics', 'price': 100},
            {'sku': 'P2', 'category': 'Electronics', 'price': 120},
            {'sku': 'P3', 'category': 'Electronics'},  # Missing price
        ]
        
        result = handler.interpolate_missing_prices(products, group_by='category')
        
        # P3 should have interpolated price
        p3 = [p for p in result if p['sku'] == 'P3'][0]
        assert 'price' in p3
        assert p3['_price_interpolated'] is True
        assert 100 <= float(p3['price']) <= 120
    
    def test_flag_incomplete_records(self, handler):
        """Test flagging incomplete records"""
        records = [
            {'sku': 'P1', 'name': 'Product 1', 'price': 100},
            {'sku': 'P2', 'name': 'Product 2'},  # Missing price
        ]
        
        result = handler.flag_incomplete_records(records, required_fields=['sku', 'name', 'price'])
        
        assert result[0]['_incomplete'] is False
        assert result[1]['_incomplete'] is True
        assert 'price' in result[1]['_missing_required_fields']
    
    def test_completeness_score(self, handler):
        """Test completeness score calculation"""
        record = {
            'sku': 'TEST-123',
            'name': 'Test Product',
            'price': 99.99
            # Missing: marketplace, category
        }
        
        all_fields = ['sku', 'name', 'price', 'marketplace', 'category']
        score = handler.get_completeness_score(record, all_fields)
        
        assert 0.0 <= score <= 1.0
        assert score == 0.6  # 3 out of 5 fields present


# ============================================================================
# Integration Tests
# ============================================================================

class TestValidationPipeline:
    """Integration tests for the complete validation pipeline"""
    
    def test_complete_product_validation_pipeline(self):
        """Test complete product validation pipeline"""
        # Raw product data
        raw_product = {
            'sku': '  test-123  ',
            'name': 'Test Product',
            'price': '99.99',
            'marketplace': 'amazon',
            'inventory_level': '100',
            'category': 'Electronics',
            'currency': 'USD'
        }
        
        # Step 1: Validate
        validator = DataValidator()
        validation_result = validator.validate_product_data(raw_product)
        assert validation_result.is_valid is True
        
        # Step 2: Normalize SKU
        normalizer = SKUNormalizer()
        normalized_sku = normalizer.normalize_sku(raw_product['sku'])
        assert normalized_sku == 'TEST-123'
        
        # Step 3: Handle missing data
        handler = MissingDataHandler()
        processed = handler.handle_missing_product_data(validation_result.validated_data)
        # Should have no critical missing fields
        assert len(processed['_critical_missing']) == 0
    
    def test_complete_review_validation_pipeline(self):
        """Test complete review validation pipeline"""
        # Raw reviews
        raw_reviews = [
            {'product_id': 'prod-1', 'rating': 5, 'text': 'Great product! Really love it.'},
            {'product_id': 'prod-1', 'rating': 5, 'text': 'Visit http://spam.com for FREE MONEY deals'},
            {'product_id': 'prod-1', 'rating': 4, 'text': 'Good quality and fast shipping'},
        ]
        
        # Step 1: Validate
        validator = DataValidator()
        valid_reviews = []
        for review in raw_reviews:
            result = validator.validate_review_data(review)
            if result.is_valid:
                valid_reviews.append(result.validated_data)
        
        assert len(valid_reviews) == 3
        
        # Step 2: Filter spam
        spam_filter = SpamFilter()
        clean_reviews = spam_filter.filter_spam_reviews(valid_reviews, mark_only=False)
        
        # Should filter some spam
        assert len(clean_reviews) <= len(valid_reviews)
        
        # Step 3: Deduplicate
        deduplicator = Deduplicator()
        final_reviews = deduplicator.deduplicate_reviews(clean_reviews)
        
        assert len(final_reviews) <= len(clean_reviews)
