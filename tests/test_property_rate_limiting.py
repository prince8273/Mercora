"""Property-based tests for rate limiting in competitor scraping"""
import pytest
import time
from hypothesis import given, strategies as st, settings
from src.ingestion.competitor_scraper import DomainRateLimiter


# Feature: ecommerce-intelligence-agent, Property 2: Rate limiting prevents scraping violations
@settings(max_examples=100, deadline=None)
@given(
    requests_per_second=st.floats(min_value=0.1, max_value=10.0),
    num_requests=st.integers(min_value=2, max_value=10)
)
def test_property_rate_limiting_prevents_violations(requests_per_second, num_requests):
    """
    **Property 2: Rate limiting prevents scraping violations**
    **Validates: Requirements 1.2**
    
    Property: When multiple requests are made to the same domain,
    the rate limiter ensures that the time between consecutive requests
    respects the configured rate limit (requests_per_second).
    
    This prevents scraping violations and respects website rate limits.
    """
    # Create rate limiter with specified rate
    limiter = DomainRateLimiter(requests_per_second=requests_per_second)
    
    # Calculate expected minimum interval between requests
    expected_min_interval = 1.0 / requests_per_second
    
    # Track request times for a single domain
    domain = "example.com"
    request_times = []
    
    # Make multiple requests to the same domain
    for _ in range(num_requests):
        start_time = time.time()
        limiter.wait_if_needed(domain)
        request_times.append(time.time())
    
    # Property 1: All requests should be recorded
    assert len(request_times) == num_requests, \
        "All requests should be tracked"
    
    # Property 2: Time intervals between consecutive requests should respect rate limit
    for i in range(1, len(request_times)):
        time_interval = request_times[i] - request_times[i-1]
        
        # Allow small tolerance for timing precision (5% or 10ms, whichever is larger)
        tolerance = max(expected_min_interval * 0.05, 0.01)
        
        assert time_interval >= (expected_min_interval - tolerance), \
            f"Request interval {time_interval:.4f}s is less than minimum {expected_min_interval:.4f}s " \
            f"(rate: {requests_per_second} req/s)"
    
    # Property 3: Total time should be at least (num_requests - 1) * min_interval
    total_time = request_times[-1] - request_times[0]
    expected_min_total = (num_requests - 1) * expected_min_interval
    
    # Allow tolerance for timing precision
    tolerance = max(expected_min_total * 0.05, 0.02)
    
    assert total_time >= (expected_min_total - tolerance), \
        f"Total time {total_time:.4f}s is less than expected minimum {expected_min_total:.4f}s"


@settings(max_examples=100)
@given(
    requests_per_second=st.floats(min_value=0.5, max_value=5.0),
    num_domains=st.integers(min_value=2, max_value=5)
)
def test_property_rate_limiting_per_domain_isolation(requests_per_second, num_domains):
    """
    **Property 2b: Rate limiting is isolated per domain**
    **Validates: Requirements 1.2**
    
    Property: Rate limiting should be applied per domain independently.
    Requests to different domains should not interfere with each other.
    """
    limiter = DomainRateLimiter(requests_per_second=requests_per_second)
    
    # Create unique domain names
    domains = [f"domain{i}.com" for i in range(num_domains)]
    
    # Make one request to each domain in quick succession
    start_time = time.time()
    for domain in domains:
        limiter.wait_if_needed(domain)
    total_time = time.time() - start_time
    
    # Property: Requests to different domains should not be rate limited
    # Total time should be minimal (not num_domains * min_interval)
    expected_min_interval = 1.0 / requests_per_second
    max_expected_time = expected_min_interval * 0.5  # Should be much faster
    
    assert total_time < max_expected_time, \
        f"Requests to different domains took {total_time:.4f}s, " \
        f"suggesting rate limiting is not per-domain"
    
    # Property: Each domain should have its own rate limit state
    assert len(limiter.last_request_times) == num_domains, \
        f"Expected {num_domains} domains tracked, got {len(limiter.last_request_times)}"


@settings(max_examples=50, deadline=None)
@given(
    requests_per_second=st.floats(min_value=0.5, max_value=5.0),
    num_requests_per_domain=st.integers(min_value=2, max_value=5)
)
def test_property_rate_limiting_multiple_domains(requests_per_second, num_requests_per_domain):
    """
    **Property 2c: Rate limiting works correctly with multiple domains**
    **Validates: Requirements 1.2**
    
    Property: When making multiple requests to multiple domains,
    each domain's rate limit is enforced independently.
    """
    limiter = DomainRateLimiter(requests_per_second=requests_per_second)
    
    domains = ["domain1.com", "domain2.com"]
    expected_min_interval = 1.0 / requests_per_second
    
    # Track request times per domain
    domain_times = {domain: [] for domain in domains}
    
    # Interleave requests to different domains
    for i in range(num_requests_per_domain):
        for domain in domains:
            limiter.wait_if_needed(domain)
            domain_times[domain].append(time.time())
    
    # Property: Each domain should have correct number of requests
    for domain in domains:
        assert len(domain_times[domain]) == num_requests_per_domain, \
            f"Domain {domain} should have {num_requests_per_domain} requests"
    
    # Property: Each domain's requests should respect rate limit
    for domain, times in domain_times.items():
        for i in range(1, len(times)):
            time_interval = times[i] - times[i-1]
            tolerance = max(expected_min_interval * 0.05, 0.01)
            
            assert time_interval >= (expected_min_interval - tolerance), \
                f"Domain {domain} request interval {time_interval:.4f}s " \
                f"is less than minimum {expected_min_interval:.4f}s"


# Edge case tests
def test_rate_limiter_first_request_no_delay():
    """Test that the first request to a domain has no delay"""
    limiter = DomainRateLimiter(requests_per_second=1.0)
    
    start_time = time.time()
    limiter.wait_if_needed("example.com")
    elapsed = time.time() - start_time
    
    # First request should be immediate (< 50ms)
    assert elapsed < 0.05, \
        f"First request should not be delayed, but took {elapsed:.4f}s"


def test_rate_limiter_very_slow_rate():
    """Test rate limiter with very slow rate (< 1 req/s)"""
    limiter = DomainRateLimiter(requests_per_second=0.5)  # 1 request every 2 seconds
    
    domain = "slow.com"
    
    # First request
    start_time = time.time()
    limiter.wait_if_needed(domain)
    first_request_time = time.time()
    
    # Second request should wait ~2 seconds
    limiter.wait_if_needed(domain)
    second_request_time = time.time()
    
    interval = second_request_time - first_request_time
    expected_interval = 2.0
    
    # Allow 10% tolerance
    assert interval >= expected_interval * 0.9, \
        f"Interval {interval:.4f}s is less than expected {expected_interval:.4f}s"


def test_rate_limiter_very_fast_rate():
    """Test rate limiter with very fast rate (> 5 req/s)"""
    limiter = DomainRateLimiter(requests_per_second=10.0)  # 10 requests per second
    
    domain = "fast.com"
    request_times = []
    
    # Make 5 requests
    for _ in range(5):
        limiter.wait_if_needed(domain)
        request_times.append(time.time())
    
    # Check intervals
    expected_interval = 0.1  # 100ms
    for i in range(1, len(request_times)):
        interval = request_times[i] - request_times[i-1]
        
        # Allow 20% tolerance for fast rates
        assert interval >= expected_interval * 0.8, \
            f"Fast rate interval {interval:.4f}s is less than expected {expected_interval:.4f}s"
