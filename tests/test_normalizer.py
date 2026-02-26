"""Tests for SKUNormalizer component"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from src.processing.normalizer import SKUNormalizer


@pytest.fixture
def normalizer():
    """Create a SKUNormalizer instance"""
    return SKUNormalizer()


class TestSKUNormalization:
    """Tests for SKU normalization"""
    
    def test_basic_normalization(self, normalizer):
        """Test basic SKU normalization"""
        sku = "test-123"
        normalized = normalizer.normalize_sku(sku)
        
        assert normalized == "TEST-123"
    
    def test_whitespace_removal(self, normalizer):
        """Test whitespace is removed"""
        sku = "TEST  123"
        normalized = normalizer.normalize_sku(sku)
        
        assert " " not in normalized
        assert normalized == "TEST123"
    
    def test_special_character_removal(self, normalizer):
        """Test special characters are removed"""
        sku = "TEST@123#456"
        normalized = normalizer.normalize_sku(sku)
        
        assert "@" not in normalized
        assert "#" not in normalized
    
    def test_amazon_asin_format(self, normalizer):
        """Test Amazon ASIN format normalization"""
        sku = "B08N5WRWNW"
        normalized = normalizer.normalize_sku(sku, marketplace='amazon')
        
        assert len(normalized) == 10
        assert normalized.isalnum()
    
    def test_ebay_item_number(self, normalizer):
        """Test eBay item number normalization"""
        sku = "123456789012"
        normalized = normalizer.normalize_sku(sku, marketplace='ebay')
        
        assert normalized.isdigit()
        assert len(normalized) == 12


class TestSKUSimilarity:
    """Tests for SKU similarity calculation"""
    
    def test_identical_skus(self, normalizer):
        """Test identical SKUs have similarity 1.0"""
        sku1 = "TEST-123"
        sku2 = "TEST-123"
        
        similarity = normalizer.calculate_sku_similarity(sku1, sku2)
        
        assert similarity == 1.0
    
    def test_completely_different_skus(self, normalizer):
        """Test completely different SKUs have low similarity"""
        sku1 = "AAAA"
        sku2 = "ZZZZ"
        
        similarity = normalizer.calculate_sku_similarity(sku1, sku2)
        
        assert similarity < 0.5
    
    def test_similar_skus(self, normalizer):
        """Test similar SKUs have high similarity"""
        sku1 = "TEST-123"
        sku2 = "TEST-124"
        
        similarity = normalizer.calculate_sku_similarity(sku1, sku2)
        
        assert similarity > 0.8


class TestProductMapping:
    """Tests for product equivalence mapping"""
    
    def test_exact_match_mapping(self, normalizer):
        """Test exact match produces high confidence"""
        mapping = normalizer.create_product_mapping(
            'TEST-123', 'amazon',
            'TEST-123', 'ebay'
        )
        
        assert mapping['confidence'] == 1.0
        assert mapping['mapping_type'] == 'exact'
    
    def test_similarity_mapping(self, normalizer):
        """Test similarity-based mapping"""
        mapping = normalizer.create_product_mapping(
            'TEST-123', 'amazon',
            'TEST-124', 'ebay'
        )
        
        assert 0.5 < mapping['confidence'] < 1.0
        assert mapping['mapping_type'] in ['similarity', 'weak']
    
    def test_low_confidence_mapping(self, normalizer):
        """Test low confidence for different SKUs"""
        mapping = normalizer.create_product_mapping(
            'AAAA', 'amazon',
            'ZZZZ', 'ebay'
        )
        
        assert mapping['confidence'] < 0.8


# ==================== Property-Based Tests ====================

@settings(max_examples=100)
@given(
    sku=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd')))
)
def test_property_normalization_consistency(sku):
    """
    **Property 4: SKU normalization produces consistent identifiers**
    **Validates: Requirements 2.1**
    
    Property: Normalizing the same SKU multiple times produces the same result
    """
    normalizer = SKUNormalizer()
    
    # Normalize twice
    normalized1 = normalizer.normalize_sku(sku)
    normalized2 = normalizer.normalize_sku(sku)
    
    # Should be identical
    assert normalized1 == normalized2


@settings(max_examples=100)
@given(
    sku=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd')))
)
def test_property_normalization_idempotent(sku):
    """
    **Property 4: SKU normalization produces consistent identifiers**
    **Validates: Requirements 2.1**
    
    Property: Normalizing an already normalized SKU doesn't change it
    """
    normalizer = SKUNormalizer()
    
    # Normalize once
    normalized1 = normalizer.normalize_sku(sku)
    
    # Normalize the result again
    normalized2 = normalizer.normalize_sku(normalized1)
    
    # Should be identical (idempotent)
    assert normalized1 == normalized2


@settings(max_examples=100)
@given(
    sku1=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    sku2=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
)
def test_property_similarity_symmetry(sku1, sku2):
    """
    **Property 4: SKU normalization produces consistent identifiers**
    **Validates: Requirements 2.1**
    
    Property: Similarity is symmetric (sim(A,B) == sim(B,A))
    """
    normalizer = SKUNormalizer()
    
    similarity_ab = normalizer.calculate_sku_similarity(sku1, sku2)
    similarity_ba = normalizer.calculate_sku_similarity(sku2, sku1)
    
    # Should be symmetric
    assert abs(similarity_ab - similarity_ba) < 0.001


@settings(max_examples=100)
@given(
    sku=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
)
def test_property_self_similarity_is_one(sku):
    """
    **Property 4: SKU normalization produces consistent identifiers**
    **Validates: Requirements 2.1**
    
    Property: A SKU is always 100% similar to itself
    """
    normalizer = SKUNormalizer()
    
    similarity = normalizer.calculate_sku_similarity(sku, sku)
    
    # Self-similarity should be 1.0
    assert similarity == 1.0


@settings(max_examples=100)
@given(
    sku1=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    sku2=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
)
def test_property_similarity_bounded(sku1, sku2):
    """
    **Property 4: SKU normalization produces consistent identifiers**
    **Validates: Requirements 2.1**
    
    Property: Similarity is always between 0 and 1
    """
    normalizer = SKUNormalizer()
    
    similarity = normalizer.calculate_sku_similarity(sku1, sku2)
    
    # Should be bounded
    assert 0.0 <= similarity <= 1.0


@settings(max_examples=100)
@given(
    sku1=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    marketplace1=st.sampled_from(['amazon', 'ebay', 'walmart', 'shopify']),
    sku2=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    marketplace2=st.sampled_from(['amazon', 'ebay', 'walmart', 'shopify'])
)
def test_property_mapping_confidence_bounded(sku1, marketplace1, sku2, marketplace2):
    """
    **Property 4: SKU normalization produces consistent identifiers**
    **Validates: Requirements 2.1**
    
    Property: Mapping confidence is always between 0 and 1
    """
    normalizer = SKUNormalizer()
    
    mapping = normalizer.create_product_mapping(sku1, marketplace1, sku2, marketplace2)
    
    # Confidence should be bounded
    assert 0.0 <= mapping['confidence'] <= 1.0
    assert 0.0 <= mapping['similarity_score'] <= 1.0


@settings(max_examples=100)
@given(
    sku=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    marketplace=st.sampled_from(['amazon', 'ebay', 'walmart', 'shopify'])
)
def test_property_exact_match_has_perfect_confidence(sku, marketplace):
    """
    **Property 4: SKU normalization produces consistent identifiers**
    **Validates: Requirements 2.1**
    
    Property: Mapping a SKU to itself has confidence 1.0
    """
    normalizer = SKUNormalizer()
    
    mapping = normalizer.create_product_mapping(sku, marketplace, sku, marketplace)
    
    # Exact match should have perfect confidence
    assert mapping['confidence'] == 1.0
    assert mapping['mapping_type'] == 'exact'
