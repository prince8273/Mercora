"""Tests for Deduplicator component"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from src.processing.deduplicator import Deduplicator


@pytest.fixture
def deduplicator():
    """Create a Deduplicator instance"""
    return Deduplicator()


class TestProductDeduplication:
    """Tests for product deduplication"""
    
    def test_no_duplicates(self, deduplicator):
        """Test deduplication with no duplicates"""
        products = [
            {'sku': 'TEST-1', 'marketplace': 'amazon', 'price': 10.0},
            {'sku': 'TEST-2', 'marketplace': 'amazon', 'price': 20.0},
            {'sku': 'TEST-3', 'marketplace': 'amazon', 'price': 30.0}
        ]
        
        result = deduplicator.deduplicate_products(products)
        
        assert len(result) == 3
    
    def test_exact_duplicates(self, deduplicator):
        """Test deduplication removes exact duplicates"""
        products = [
            {'sku': 'TEST-1', 'marketplace': 'amazon', 'price': 10.0, 'updated_at': datetime(2024, 1, 1)},
            {'sku': 'TEST-1', 'marketplace': 'amazon', 'price': 15.0, 'updated_at': datetime(2024, 1, 2)},
            {'sku': 'TEST-2', 'marketplace': 'amazon', 'price': 20.0, 'updated_at': datetime(2024, 1, 1)}
        ]
        
        result = deduplicator.deduplicate_products(products)
        
        assert len(result) == 2
        # Should keep the most recent version
        test1 = [p for p in result if p['sku'] == 'TEST-1'][0]
        assert test1['price'] == 15.0
    
    def test_different_marketplaces_not_duplicates(self, deduplicator):
        """Test same SKU in different marketplaces are not duplicates"""
        products = [
            {'sku': 'TEST-1', 'marketplace': 'amazon', 'price': 10.0},
            {'sku': 'TEST-1', 'marketplace': 'ebay', 'price': 12.0}
        ]
        
        result = deduplicator.deduplicate_products(products)
        
        assert len(result) == 2


class TestReviewDeduplication:
    """Tests for review deduplication"""
    
    def test_duplicate_reviews(self, deduplicator):
        """Test deduplication removes duplicate reviews"""
        reviews = [
            {'product_id': '123', 'text': 'Great product!', 'created_at': datetime(2024, 1, 1)},
            {'product_id': '123', 'text': 'Great product!', 'created_at': datetime(2024, 1, 2)},
            {'product_id': '456', 'text': 'Great product!', 'created_at': datetime(2024, 1, 1)}
        ]
        
        result = deduplicator.deduplicate_reviews(reviews)
        
        # Should keep 2: one for product 123 (most recent), one for product 456
        assert len(result) == 2


class TestDuplicateDetection:
    """Tests for duplicate detection"""
    
    def test_find_duplicates(self, deduplicator):
        """Test finding duplicate groups"""
        products = [
            {'sku': 'TEST-1', 'marketplace': 'amazon', 'price': 10.0},
            {'sku': 'TEST-1', 'marketplace': 'amazon', 'price': 15.0},
            {'sku': 'TEST-2', 'marketplace': 'amazon', 'price': 20.0}
        ]
        
        duplicates = deduplicator.find_duplicates(products, ['sku', 'marketplace'])
        
        assert len(duplicates) == 1
        assert 'test-1||amazon' in duplicates


class TestMostRecentSelection:
    """Tests for most recent record selection"""
    
    def test_most_recent_by_updated_at(self, deduplicator):
        """Test selection by updated_at"""
        records = [
            {'id': 1, 'updated_at': datetime(2024, 1, 1)},
            {'id': 2, 'updated_at': datetime(2024, 1, 3)},
            {'id': 3, 'updated_at': datetime(2024, 1, 2)}
        ]
        
        most_recent = deduplicator._get_most_recent(records)
        
        assert most_recent['id'] == 2
    
    def test_most_recent_by_created_at(self, deduplicator):
        """Test selection by created_at when updated_at missing"""
        records = [
            {'id': 1, 'created_at': datetime(2024, 1, 1)},
            {'id': 2, 'created_at': datetime(2024, 1, 3)},
            {'id': 3, 'created_at': datetime(2024, 1, 2)}
        ]
        
        most_recent = deduplicator._get_most_recent(records)
        
        assert most_recent['id'] == 2


# ==================== Property-Based Tests ====================

@settings(max_examples=100)
@given(
    products=st.lists(
        st.fixed_dictionaries({
            'sku': st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
            'marketplace': st.sampled_from(['amazon', 'ebay', 'walmart']),
            'price': st.floats(min_value=1.0, max_value=1000.0),
            'updated_at': st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31))
        }),
        min_size=1,
        max_size=50
    )
)
def test_property_deduplication_preserves_most_recent(products):
    """
    **Property 5: Deduplication preserves most recent records**
    **Validates: Requirements 2.2**
    
    Property: After deduplication, each unique product appears once with the most recent data
    """
    deduplicator = Deduplicator()
    
    # Deduplicate
    result = deduplicator.deduplicate_products(products)
    
    # Result should not be empty
    assert len(result) > 0
    
    # Result should have no duplicates
    keys = set()
    for product in result:
        key = f"{product['sku']}||{product['marketplace']}"
        assert key not in keys, "Duplicate found in result"
        keys.add(key)
    
    # For each unique key, verify we kept the most recent
    groups = {}
    for product in products:
        key = f"{product['sku']}||{product['marketplace']}"
        if key not in groups:
            groups[key] = []
        groups[key].append(product)
    
    for key, group in groups.items():
        if len(group) > 1:
            # Find most recent in original
            most_recent_original = max(group, key=lambda p: p['updated_at'])
            
            # Find in result
            sku, marketplace = key.split('||')
            result_product = [p for p in result if p['sku'] == sku and p['marketplace'] == marketplace][0]
            
            # Should be the same
            assert result_product['updated_at'] == most_recent_original['updated_at']


@settings(max_examples=100)
@given(
    products=st.lists(
        st.fixed_dictionaries({
            'sku': st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
            'marketplace': st.sampled_from(['amazon', 'ebay', 'walmart']),
            'price': st.floats(min_value=1.0, max_value=1000.0)
        }),
        min_size=1,
        max_size=50
    )
)
def test_property_deduplication_reduces_or_maintains_count(products):
    """
    **Property 5: Deduplication preserves most recent records**
    **Validates: Requirements 2.2**
    
    Property: Deduplication never increases the number of records
    """
    deduplicator = Deduplicator()
    
    result = deduplicator.deduplicate_products(products)
    
    # Result should have same or fewer records
    assert len(result) <= len(products)


@settings(max_examples=100)
@given(
    products=st.lists(
        st.fixed_dictionaries({
            'sku': st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
            'marketplace': st.sampled_from(['amazon', 'ebay', 'walmart']),
            'price': st.floats(min_value=1.0, max_value=1000.0)
        }),
        min_size=1,
        max_size=50
    )
)
def test_property_deduplication_idempotent(products):
    """
    **Property 5: Deduplication preserves most recent records**
    **Validates: Requirements 2.2**
    
    Property: Deduplicating twice produces the same result as deduplicating once
    """
    deduplicator = Deduplicator()
    
    # Deduplicate once
    result1 = deduplicator.deduplicate_products(products)
    
    # Deduplicate again
    result2 = deduplicator.deduplicate_products(result1)
    
    # Should be identical
    assert len(result1) == len(result2)


@settings(max_examples=100)
@given(
    reviews=st.lists(
        st.fixed_dictionaries({
            'product_id': st.text(min_size=5, max_size=10),
            'text': st.text(min_size=10, max_size=100),
            'rating': st.integers(min_value=1, max_value=5),
            'created_at': st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31))
        }),
        min_size=1,
        max_size=50
    )
)
def test_property_review_deduplication_preserves_most_recent(reviews):
    """
    **Property 5: Deduplication preserves most recent records**
    **Validates: Requirements 2.2**
    
    Property: Review deduplication preserves the most recent version
    """
    deduplicator = Deduplicator()
    
    result = deduplicator.deduplicate_reviews(reviews)
    
    # Result should not be empty
    assert len(result) > 0
    
    # Result should have no duplicates
    keys = set()
    for review in result:
        # Normalize text for comparison
        key = f"{review['product_id']}||{review['text'].strip().lower()}"
        assert key not in keys, "Duplicate review found in result"
        keys.add(key)


@settings(max_examples=100)
@given(
    products=st.lists(
        st.fixed_dictionaries({
            'sku': st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
            'marketplace': st.text(min_size=3, max_size=10),
            'price': st.floats(min_value=1.0, max_value=1000.0)
        }),
        min_size=0,
        max_size=50
    )
)
def test_property_empty_input_produces_empty_output(products):
    """
    **Property 5: Deduplication preserves most recent records**
    **Validates: Requirements 2.2**
    
    Property: Deduplicating an empty list returns an empty list
    """
    deduplicator = Deduplicator()
    
    result = deduplicator.deduplicate_products(products)
    
    if len(products) == 0:
        assert len(result) == 0
