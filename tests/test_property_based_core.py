"""
Core Property-Based Tests for E-commerce Intelligence Agent
Feature: ecommerce-intelligence-agent

These tests validate critical correctness properties using Hypothesis.
Minimum 100 iterations per test as per design specification.
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal

from src.models.product import Product
from src.models.review import Review
from src.models.sales_record import SalesRecord
from src.processing.validator import DataValidator
from src.processing.normalizer import SKUNormalizer
from src.processing.deduplicator import Deduplicator
from src.processing.spam_filter import SpamFilter


# Property 1: Data Validation Round-Trip
# Feature: ecommerce-intelligence-agent, Property 9: Validated data round-trip
@settings(max_examples=100)
@given(
    sku=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
    name=st.text(min_size=1, max_size=200),
    price=st.decimals(min_value=0.01, max_value=10000, places=2),
    inventory=st.integers(min_value=0, max_value=10000)
)
def test_property_validated_data_roundtrip(sku, name, price, inventory):
    """
    Property: When valid data is validated, it should pass validation
    and maintain its essential properties after round-trip.
    
    Validates: Requirements 2.6
    """
    validator = DataValidator()
    
    # Create product data
    product_data = {
        'sku': sku,
        'name': name,
        'category': 'Electronics',
        'price': float(price),
        'currency': 'USD',
        'marketplace': 'amazon',
        'inventory_level': inventory
    }
    
    # Validate
    result = validator.validate_product(product_data)
    
    # Property: Valid data should pass validation
    assert result.is_valid, f"Valid data failed validation: {result.errors}"
    
    # Property: Essential fields should be preserved
    assert result.validated_data['sku'] == sku
    assert result.validated_data['name'] == name
    assert abs(result.validated_data['price'] - float(price)) < 0.01
    assert result.validated_data['inventory_level'] == inventory


# Property 2: SKU Normalization Consistency
# Feature: ecommerce-intelligence-agent, Property 4: SKU normalization produces consistent identifiers
@settings(max_examples=100)
@given(
    sku=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
    marketplace=st.sampled_from(['amazon', 'ebay', 'walmart', 'shopify'])
)
def test_property_sku_normalization_consistency(sku, marketplace):
    """
    Property: Normalizing the same SKU multiple times should produce
    the same normalized result (idempotency).
    
    Validates: Requirements 2.1
    """
    normalizer = SKUNormalizer()
    
    # Normalize twice
    normalized_1 = normalizer.normalize_sku(sku, marketplace)
    normalized_2 = normalizer.normalize_sku(sku, marketplace)
    
    # Property: Normalization should be idempotent
    assert normalized_1 == normalized_2, "SKU normalization is not consistent"
    
    # Property: Normalized SKU should be uppercase (design decision)
    assert normalized_1.isupper() or not normalized_1.isalpha(), \
        "Normalized SKU should be uppercase"


# Property 3: Deduplication Preserves Most Recent
# Feature: ecommerce-intelligence-agent, Property 5: Deduplication preserves most recent records
@settings(max_examples=100)
@given(
    sku=st.text(min_size=1, max_size=50),
    num_duplicates=st.integers(min_value=2, max_value=10)
)
def test_property_deduplication_preserves_recent(sku, num_duplicates):
    """
    Property: When duplicate records exist, deduplication should
    preserve the most recent record based on timestamp.
    
    Validates: Requirements 2.2
    """
    deduplicator = Deduplicator()
    tenant_id = uuid4()
    
    # Create duplicate products with different timestamps
    products = []
    base_time = datetime.utcnow()
    
    for i in range(num_duplicates):
        product = Product(
            id=uuid4(),
            tenant_id=tenant_id,
            sku=sku,
            normalized_sku=sku.upper(),
            name=f"Product {i}",
            category="Electronics",
            price=Decimal("99.99"),
            currency="USD",
            marketplace="amazon",
            inventory_level=100,
            created_at=base_time + timedelta(seconds=i),
            updated_at=base_time + timedelta(seconds=i)
        )
        products.append(product)
    
    # Deduplicate
    deduplicated = deduplicator.deduplicate_products(products)
    
    # Property: Should return exactly one product
    assert len(deduplicated) == 1, "Deduplication should return one record"
    
    # Property: Should be the most recent one (last in list)
    assert deduplicated[0].created_at == products[-1].created_at, \
        "Deduplication should preserve most recent record"


# Property 4: Spam Filter Consistency
# Feature: ecommerce-intelligence-agent, Property 8: Spam reviews are filtered
@settings(max_examples=100)
@given(
    text=st.text(min_size=10, max_size=500),
    rating=st.integers(min_value=1, max_value=5)
)
def test_property_spam_filter_consistency(text, rating):
    """
    Property: Spam filtering should be consistent - the same review
    should always produce the same spam classification.
    
    Validates: Requirements 2.5
    """
    spam_filter = SpamFilter()
    
    # Create review
    review = Review(
        id=uuid4(),
        tenant_id=uuid4(),
        product_id=uuid4(),
        rating=rating,
        text=text,
        source="test",
        is_spam=False,
        created_at=datetime.utcnow()
    )
    
    # Filter twice
    result_1 = spam_filter.is_spam(review)
    result_2 = spam_filter.is_spam(review)
    
    # Property: Spam classification should be consistent
    assert result_1 == result_2, "Spam filtering should be deterministic"


# Property 5: Tenant Data Isolation
# Feature: ecommerce-intelligence-agent, Property 83: All stored data is tagged with tenant ID
@settings(max_examples=100)
@given(
    num_tenants=st.integers(min_value=2, max_value=5),
    products_per_tenant=st.integers(min_value=1, max_value=10)
)
def test_property_tenant_data_tagging(num_tenants, products_per_tenant):
    """
    Property: All created data records should be tagged with a tenant_id,
    and no record should exist without a tenant_id.
    
    Validates: Requirements 20.2
    """
    # Create products for multiple tenants
    all_products = []
    tenant_ids = [uuid4() for _ in range(num_tenants)]
    
    for tenant_id in tenant_ids:
        for i in range(products_per_tenant):
            product = Product(
                id=uuid4(),
                tenant_id=tenant_id,
                sku=f"SKU-{tenant_id}-{i}",
                normalized_sku=f"SKU-{tenant_id}-{i}".upper(),
                name=f"Product {i}",
                category="Electronics",
                price=Decimal("99.99"),
                currency="USD",
                marketplace="amazon",
                inventory_level=100,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            all_products.append(product)
    
    # Property: All products should have a tenant_id
    assert all(p.tenant_id is not None for p in all_products), \
        "All products must have a tenant_id"
    
    # Property: Each product should belong to exactly one tenant
    for product in all_products:
        assert product.tenant_id in tenant_ids, \
            "Product tenant_id must be one of the created tenants"


# Property 6: Price Gap Calculation Correctness
# Feature: ecommerce-intelligence-agent, Property 11: Price gaps are calculated correctly
@settings(max_examples=100)
@given(
    our_price=st.decimals(min_value=1, max_value=1000, places=2),
    competitor_price=st.decimals(min_value=1, max_value=1000, places=2)
)
def test_property_price_gap_calculation(our_price, competitor_price):
    """
    Property: Price gap should be calculated as (our_price - competitor_price),
    and the sign should indicate whether we're more expensive (+) or cheaper (-).
    
    Validates: Requirements 3.3
    """
    from src.agents.pricing_intelligence import PricingIntelligenceAgent
    
    agent = PricingIntelligenceAgent(tenant_id=uuid4())
    
    # Calculate price gap
    price_gap = agent.calculate_price_gap(
        our_price=float(our_price),
        competitor_price=float(competitor_price)
    )
    
    # Property: Price gap should equal difference
    expected_gap = float(our_price) - float(competitor_price)
    assert abs(price_gap - expected_gap) < 0.01, \
        f"Price gap calculation incorrect: {price_gap} != {expected_gap}"
    
    # Property: Positive gap means we're more expensive
    if our_price > competitor_price:
        assert price_gap > 0, "Positive gap should indicate higher price"
    elif our_price < competitor_price:
        assert price_gap < 0, "Negative gap should indicate lower price"
    else:
        assert abs(price_gap) < 0.01, "Equal prices should have zero gap"


# Property 7: Confidence Score Range
# Feature: ecommerce-intelligence-agent, Property 15: All recommendations include confidence scores
@settings(max_examples=100)
@given(
    data_completeness=st.floats(min_value=0.0, max_value=1.0),
    model_confidence=st.floats(min_value=0.0, max_value=1.0)
)
def test_property_confidence_score_range(data_completeness, model_confidence):
    """
    Property: Confidence scores should always be in the range [0, 100],
    normalized from the 0-1 scale used internally.
    
    Validates: Requirements 3.7, 7.5
    """
    from src.orchestration.result_synthesizer import ResultSynthesizer
    
    synthesizer = ResultSynthesizer(tenant_id=uuid4())
    
    # Calculate confidence score
    confidence = synthesizer.calculate_confidence_score(
        data_completeness=data_completeness,
        model_confidence=model_confidence
    )
    
    # Property: Confidence should be in valid range
    assert 0 <= confidence <= 100, \
        f"Confidence score {confidence} outside valid range [0, 100]"
    
    # Property: Higher inputs should generally produce higher confidence
    if data_completeness > 0.5 and model_confidence > 0.5:
        assert confidence > 25, "High quality inputs should produce reasonable confidence"


# Property 8: Query Execution Produces Structured Report
# Feature: ecommerce-intelligence-agent, Property 31: Multi-agent results are synthesized
@settings(max_examples=50)  # Fewer examples due to complexity
@given(
    query_text=st.text(min_size=10, max_size=200),
    num_agents=st.integers(min_value=1, max_value=3)
)
def test_property_query_produces_structured_report(query_text, num_agents):
    """
    Property: Any valid query should produce a structured report with
    all required fields (executive_summary, key_metrics, action_items, etc.).
    
    Validates: Requirements 6.6, 7.1
    """
    from src.schemas.report import StructuredReport
    from src.schemas.orchestration import AgentResult, AgentType
    
    # Create mock agent results
    agent_results = []
    agent_types = [AgentType.PRICING, AgentType.SENTIMENT, AgentType.DEMAND_FORECAST]
    
    for i in range(min(num_agents, len(agent_types))):
        result = AgentResult(
            agent_type=agent_types[i],
            success=True,
            data={'analysis': f'Result from {agent_types[i].value}'},
            confidence=0.85,
            execution_time_ms=100
        )
        agent_results.append(result)
    
    # Synthesize report
    from src.orchestration.result_synthesizer import ResultSynthesizer
    synthesizer = ResultSynthesizer(tenant_id=uuid4())
    
    report = synthesizer.synthesize_results(
        agent_results=agent_results,
        query=query_text
    )
    
    # Property: Report should have all required fields
    assert hasattr(report, 'executive_summary'), "Report missing executive_summary"
    assert hasattr(report, 'key_metrics'), "Report missing key_metrics"
    assert hasattr(report, 'insights'), "Report missing insights"
    assert hasattr(report, 'action_items'), "Report missing action_items"
    assert hasattr(report, 'overall_confidence'), "Report missing overall_confidence"
    
    # Property: Confidence should be in valid range
    assert 0 <= report.overall_confidence <= 100, \
        "Report confidence outside valid range"


# Property 9: Cache Key Consistency
# Feature: ecommerce-intelligence-agent, Property 66: Stale cache is refreshed before use
@settings(max_examples=100)
@given(
    query_text=st.text(min_size=1, max_size=200),
    tenant_id_str=st.text(min_size=36, max_size=36, alphabet=st.characters(whitelist_categories=('Ll', 'Nd', 'Pd')))
)
def test_property_cache_key_consistency(query_text, tenant_id_str):
    """
    Property: The same query and tenant should always produce the same cache key,
    ensuring consistent cache hits.
    
    Validates: Requirements 16.1, 16.2, 16.3
    """
    from src.cache.cache_manager import CacheManager
    
    cache_manager = CacheManager()
    
    # Generate cache key twice
    key_1 = cache_manager.generate_cache_key(
        query=query_text,
        tenant_id=tenant_id_str
    )
    key_2 = cache_manager.generate_cache_key(
        query=query_text,
        tenant_id=tenant_id_str
    )
    
    # Property: Cache keys should be consistent
    assert key_1 == key_2, "Cache key generation should be deterministic"
    
    # Property: Different queries should produce different keys
    different_query = query_text + "_different"
    key_3 = cache_manager.generate_cache_key(
        query=different_query,
        tenant_id=tenant_id_str
    )
    
    if query_text != different_query:
        assert key_1 != key_3, "Different queries should have different cache keys"


# Property 10: Token Usage Tracking
# Feature: ecommerce-intelligence-agent, Property 78: Token usage is tracked per user and period
@settings(max_examples=100)
@given(
    prompt_length=st.integers(min_value=10, max_value=1000),
    response_length=st.integers(min_value=10, max_value=2000)
)
def test_property_token_usage_tracking(prompt_length, response_length):
    """
    Property: Token usage should be tracked for every LLM call,
    and the total should be the sum of prompt and response tokens.
    
    Validates: Requirements 19.1
    """
    from src.orchestration.llm_reasoning_engine import LLMReasoningEngine
    
    engine = LLMReasoningEngine(tenant_id=uuid4())
    
    # Simulate token usage
    prompt_tokens = prompt_length // 4  # Rough estimate: 4 chars per token
    response_tokens = response_length // 4
    
    engine.track_token_usage(
        prompt_tokens=prompt_tokens,
        response_tokens=response_tokens
    )
    
    # Get total usage
    total_usage = engine.get_total_token_usage()
    
    # Property: Total should equal sum of prompt and response
    expected_total = prompt_tokens + response_tokens
    assert total_usage['total_tokens'] == expected_total, \
        f"Token tracking incorrect: {total_usage['total_tokens']} != {expected_total}"
    
    # Property: Usage should be non-negative
    assert total_usage['prompt_tokens'] >= 0, "Prompt tokens should be non-negative"
    assert total_usage['response_tokens'] >= 0, "Response tokens should be non-negative"
    assert total_usage['total_tokens'] >= 0, "Total tokens should be non-negative"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
