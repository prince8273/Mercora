"""Tests for MissingDataHandler component"""
import pytest
from hypothesis import given, strategies as st, settings
from src.processing.missing_data_handler import MissingDataHandler


@pytest.fixture
def handler():
    """Create a MissingDataHandler instance"""
    return MissingDataHandler()


class TestProductMissingData:
    """Tests for product missing data handling"""
    
    def test_complete_product(self, handler):
        """Test handling of complete product data"""
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
        
        assert not result['_has_missing_data']
        assert len(result['_missing_fields']) == 0
        assert len(result['_critical_missing']) == 0
    
    def test_missing_optional_fields(self, handler):
        """Test handling of missing optional fields"""
        product = {
            'sku': 'TEST-123',
            'name': 'Test Product',
            'price': 99.99,
            'marketplace': 'amazon'
        }
        
        result = handler.handle_missing_product_data(product, apply_defaults=True)
        
        assert result['_has_missing_data']
        assert 'category' in result['_missing_fields']
        assert 'inventory_level' in result['_missing_fields']
        # Defaults should be applied
        assert result['category'] == 'Uncategorized'
        assert result['currency'] == 'USD'
    
    def test_missing_critical_fields(self, handler):
        """Test handling of missing critical fields"""
        product = {
            'name': 'Test Product'
        }
        
        result = handler.handle_missing_product_data(product)
        
        assert result['_has_missing_data']
        assert 'sku' in result['_critical_missing']
        assert 'price' in result['_critical_missing']
        assert 'marketplace' in result['_critical_missing']


class TestReviewMissingData:
    """Tests for review missing data handling"""
    
    def test_complete_review(self, handler):
        """Test handling of complete review data"""
        review = {
            'product_id': '123',
            'rating': 5,
            'text': 'Great product!',
            'sentiment': 'positive',
            'is_spam': False,
            'verified_purchase': True
        }
        
        result = handler.handle_missing_review_data(review)
        
        assert not result['_has_missing_data']
        assert len(result['_missing_fields']) == 0
    
    def test_missing_optional_review_fields(self, handler):
        """Test handling of missing optional review fields"""
        review = {
            'product_id': '123',
            'rating': 5,
            'text': 'Great product!'
        }
        
        result = handler.handle_missing_review_data(review, apply_defaults=True)
        
        assert result['_has_missing_data']
        assert 'sentiment' in result['_missing_fields']
        # Defaults should be applied
        assert result['is_spam'] == False


class TestPriceInterpolation:
    """Tests for price interpolation"""
    
    def test_interpolate_by_category(self, handler):
        """Test price interpolation by category"""
        products = [
            {'sku': '1', 'category': 'Electronics', 'price': 100.0},
            {'sku': '2', 'category': 'Electronics', 'price': 200.0},
            {'sku': '3', 'category': 'Electronics', 'price': None},
            {'sku': '4', 'category': 'Books', 'price': 10.0},
            {'sku': '5', 'category': 'Books', 'price': None}
        ]
        
        result = handler.interpolate_missing_prices(products, group_by='category')
        
        # Electronics product should have interpolated price around 150
        electronics_product = [p for p in result if p['sku'] == '3'][0]
        assert electronics_product['price'] is not None
        assert electronics_product['_price_interpolated']
        assert 100 <= float(electronics_product['price']) <= 200
        
        # Books product should have interpolated price around 10
        books_product = [p for p in result if p['sku'] == '5'][0]
        assert books_product['price'] is not None
        assert books_product['_price_interpolated']


class TestCompletenessScore:
    """Tests for completeness score calculation"""
    
    def test_complete_record_score(self, handler):
        """Test completeness score for complete record"""
        record = {
            'field1': 'value1',
            'field2': 'value2',
            'field3': 'value3'
        }
        
        score = handler.get_completeness_score(record, ['field1', 'field2', 'field3'])
        
        assert score == 1.0
    
    def test_partial_record_score(self, handler):
        """Test completeness score for partial record"""
        record = {
            'field1': 'value1',
            'field2': None,
            'field3': 'value3'
        }
        
        score = handler.get_completeness_score(record, ['field1', 'field2', 'field3'])
        
        assert score == 2.0 / 3.0
    
    def test_empty_record_score(self, handler):
        """Test completeness score for empty record"""
        record = {}
        
        score = handler.get_completeness_score(record, ['field1', 'field2', 'field3'])
        
        assert score == 0.0


# ==================== Property-Based Tests ====================

@settings(max_examples=100)
@given(
    products=st.lists(
        st.fixed_dictionaries({
            'sku': st.text(min_size=3, max_size=20),
            'name': st.text(min_size=2, max_size=50),
            'price': st.floats(min_value=1.0, max_value=1000.0),
            'marketplace': st.sampled_from(['amazon', 'ebay', 'walmart']),
            'category': st.one_of(st.none(), st.text(min_size=3, max_size=20)),
            'inventory_level': st.one_of(st.none(), st.integers(min_value=0, max_value=1000))
        }),
        min_size=1,
        max_size=20
    )
)
def test_property_missing_data_flagged(products):
    """
    **Property 6: Missing data is flagged and handled**
    **Validates: Requirements 2.3**
    
    Property: All products with missing data are flagged appropriately
    """
    handler = MissingDataHandler()
    
    for product in products:
        result = handler.handle_missing_product_data(product)
        
        # Check if missing data flag is accurate
        has_missing = (
            product.get('category') is None or
            product.get('inventory_level') is None
        )
        
        if has_missing:
            assert result['_has_missing_data']
            assert len(result['_missing_fields']) > 0
        
        # Metadata fields should always be present
        assert '_missing_fields' in result
        assert '_critical_missing' in result
        assert '_has_missing_data' in result


@settings(max_examples=100)
@given(
    products=st.lists(
        st.fixed_dictionaries({
            'sku': st.text(min_size=3, max_size=20),
            'name': st.text(min_size=2, max_size=50),
            'price': st.floats(min_value=1.0, max_value=1000.0),
            'marketplace': st.sampled_from(['amazon', 'ebay', 'walmart'])
        }),
        min_size=1,
        max_size=20
    )
)
def test_property_defaults_applied_consistently(products):
    """
    **Property 6: Missing data is flagged and handled**
    **Validates: Requirements 2.3**
    
    Property: Default values are applied consistently
    """
    handler = MissingDataHandler()
    
    for product in products:
        result = handler.handle_missing_product_data(product, apply_defaults=True)
        
        # If category was missing, default should be applied
        if 'category' not in product or product.get('category') is None:
            assert result['category'] == 'Uncategorized'
        
        # If currency was missing, default should be applied
        if 'currency' not in product or product.get('currency') is None:
            assert result['currency'] == 'USD'


@settings(max_examples=100)
@given(
    reviews=st.lists(
        st.fixed_dictionaries({
            'product_id': st.text(min_size=5, max_size=20),
            'rating': st.integers(min_value=1, max_value=5),
            'text': st.text(min_size=10, max_size=200),
            'sentiment': st.one_of(st.none(), st.sampled_from(['positive', 'negative', 'neutral'])),
            'is_spam': st.one_of(st.none(), st.booleans())
        }),
        min_size=1,
        max_size=20
    )
)
def test_property_review_missing_data_flagged(reviews):
    """
    **Property 6: Missing data is flagged and handled**
    **Validates: Requirements 2.3**
    
    Property: All reviews with missing data are flagged appropriately
    """
    handler = MissingDataHandler()
    
    for review in reviews:
        result = handler.handle_missing_review_data(review)
        
        # Check if missing data flag is accurate
        has_missing = (
            review.get('sentiment') is None or
            review.get('is_spam') is None
        )
        
        if has_missing:
            assert result['_has_missing_data']
            assert len(result['_missing_fields']) > 0
        
        # Metadata fields should always be present
        assert '_missing_fields' in result
        assert '_critical_missing' in result
        assert '_has_missing_data' in result


@settings(max_examples=100)
@given(
    record=st.fixed_dictionaries({
        'field1': st.one_of(st.none(), st.text(min_size=1, max_size=10)),
        'field2': st.one_of(st.none(), st.text(min_size=1, max_size=10)),
        'field3': st.one_of(st.none(), st.text(min_size=1, max_size=10)),
        'field4': st.one_of(st.none(), st.text(min_size=1, max_size=10))
    })
)
def test_property_completeness_score_bounded(record):
    """
    **Property 6: Missing data is flagged and handled**
    **Validates: Requirements 2.3**
    
    Property: Completeness score is always between 0 and 1
    """
    handler = MissingDataHandler()
    
    all_fields = ['field1', 'field2', 'field3', 'field4']
    score = handler.get_completeness_score(record, all_fields)
    
    # Score should be bounded
    assert 0.0 <= score <= 1.0


@settings(max_examples=100)
@given(
    products=st.lists(
        st.fixed_dictionaries({
            'sku': st.text(min_size=3, max_size=20),
            'category': st.text(min_size=3, max_size=20),
            'price': st.one_of(st.none(), st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
        }),
        min_size=2,
        max_size=20,
        unique_by=lambda p: p['sku']  # Ensure unique SKUs
    )
)
def test_property_interpolation_preserves_existing_prices(products):
    """
    **Property 6: Missing data is flagged and handled**
    **Validates: Requirements 2.3**
    
    Property: Price interpolation never changes existing prices
    """
    handler = MissingDataHandler()
    
    # Make a copy of products to avoid mutation issues
    import copy
    products_copy = copy.deepcopy(products)
    
    # Store original prices
    original_prices = {p['sku']: p.get('price') for p in products_copy}
    
    # Interpolate
    result = handler.interpolate_missing_prices(products_copy, group_by='category')
    
    # Check that existing prices weren't changed
    for product in result:
        sku = product['sku']
        original_price = original_prices[sku]
        
        if original_price is not None:
            # Existing price should be unchanged (within floating point tolerance)
            result_price = float(product['price'])
            assert abs(result_price - float(original_price)) < 0.01, \
                f"Price changed from {original_price} to {result_price}"
