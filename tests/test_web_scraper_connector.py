"""Unit tests for web scraper connector"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from uuid import uuid4

from src.ingestion.connectors.web_scraper_connector import (
    WebScraperConnector,
    RobotsTxtChecker,
    DomainRateLimiter
)
from src.ingestion.base import RawRecord


class TestRobotsTxtChecker:
    """Test suite for robots.txt checker"""
    
    @pytest.fixture
    def checker(self):
        """Fixture for robots.txt checker"""
        return RobotsTxtChecker(user_agent="TestBot/1.0")
    
    def test_checker_initialization(self, checker):
        """Test checker initializes correctly"""
        assert checker.user_agent == "TestBot/1.0"
        assert checker.cache_timeout == 3600
        assert len(checker.parsers) == 0
    
    @patch('urllib.robotparser.RobotFileParser.read')
    @patch('urllib.robotparser.RobotFileParser.can_fetch')
    def test_is_allowed_returns_true(self, mock_can_fetch, mock_read, checker):
        """Test is_allowed returns True when allowed"""
        mock_can_fetch.return_value = True
        
        result = checker.is_allowed("https://example.com/product/123")
        
        assert result is True
        mock_read.assert_called_once()
    
    @patch('urllib.robotparser.RobotFileParser.read')
    @patch('urllib.robotparser.RobotFileParser.can_fetch')
    def test_is_allowed_returns_false(self, mock_can_fetch, mock_read, checker):
        """Test is_allowed returns False when blocked"""
        mock_can_fetch.return_value = False
        
        result = checker.is_allowed("https://example.com/admin")
        
        assert result is False
    
    @patch('urllib.robotparser.RobotFileParser.read')
    def test_is_allowed_caches_results(self, mock_read, checker):
        """Test that robots.txt results are cached"""
        url1 = "https://example.com/product/1"
        url2 = "https://example.com/product/2"
        
        checker.is_allowed(url1)
        checker.is_allowed(url2)
        
        # Should only read once for same domain
        assert mock_read.call_count == 1
    
    @patch('urllib.robotparser.RobotFileParser.read')
    def test_is_allowed_handles_errors_gracefully(self, mock_read, checker):
        """Test that errors default to allowing access"""
        mock_read.side_effect = Exception("Network error")
        
        result = checker.is_allowed("https://example.com/product/123")
        
        # Should default to True on error
        assert result is True


class TestDomainRateLimiter:
    """Test suite for domain rate limiter"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes correctly"""
        limiter = DomainRateLimiter(requests_per_second=2.0)
        
        assert limiter.requests_per_second == 2.0
        assert limiter.min_interval == 0.5
        assert len(limiter.last_request_times) == 0
    
    def test_wait_if_needed_first_request(self):
        """Test that first request doesn't wait"""
        limiter = DomainRateLimiter(requests_per_second=1.0)
        
        import time
        start = time.time()
        limiter.wait_if_needed("example.com")
        duration = time.time() - start
        
        # Should not wait on first request
        assert duration < 0.1
    
    def test_wait_if_needed_respects_rate_limit(self):
        """Test that rate limiting works"""
        limiter = DomainRateLimiter(requests_per_second=10.0)  # 0.1s interval
        
        import time
        limiter.wait_if_needed("example.com")
        
        start = time.time()
        limiter.wait_if_needed("example.com")
        duration = time.time() - start
        
        # Should wait approximately 0.1s (with jitter)
        assert 0.08 <= duration <= 0.15
    
    def test_wait_if_needed_different_domains(self):
        """Test that different domains don't interfere"""
        limiter = DomainRateLimiter(requests_per_second=1.0)
        
        import time
        limiter.wait_if_needed("example.com")
        
        start = time.time()
        limiter.wait_if_needed("other.com")
        duration = time.time() - start
        
        # Should not wait for different domain
        assert duration < 0.1


class TestWebScraperConnector:
    """Test suite for web scraper connector"""
    
    @pytest.fixture
    def tenant_id(self):
        """Fixture for tenant ID"""
        return uuid4()
    
    @pytest.fixture
    def sample_urls(self):
        """Fixture for sample URLs"""
        return [
            "https://example.com/product/1",
            "https://example.com/product/2",
            "https://other.com/item/abc"
        ]
    
    @pytest.fixture
    def mock_html(self):
        """Fixture for mock HTML response"""
        return """
        <html>
            <head><title>Test Product</title></head>
            <body>
                <h1>Wireless Mouse</h1>
                <span class="price">$29.99</span>
                <div class="product-description">
                    Great wireless mouse with ergonomic design.
                </div>
                <img src="/images/product1.jpg" />
                <div>In Stock</div>
                <span class="rating">4.5</span>
            </body>
        </html>
        """
    
    def test_connector_initialization(self, tenant_id, sample_urls):
        """Test connector initializes correctly"""
        connector = WebScraperConnector(
            tenant_id=tenant_id,
            urls=sample_urls,
            source_name="test_scraper",
            user_agent="TestBot/1.0"
        )
        
        assert connector.tenant_id == tenant_id
        assert connector.source_name == "test_scraper"
        assert connector.urls == sample_urls
        assert connector.user_agent == "TestBot/1.0"
        assert connector.timeout == 10
    
    @patch('src.ingestion.connectors.web_scraper_connector.requests.get')
    @patch.object(RobotsTxtChecker, 'is_allowed')
    def test_fetch_scrapes_urls(self, mock_is_allowed, mock_get, tenant_id, sample_urls, mock_html):
        """Test fetch scrapes URLs and yields records"""
        mock_is_allowed.return_value = True
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        connector = WebScraperConnector(
            tenant_id=tenant_id,
            urls=sample_urls[:1],  # Just test one URL
            source_name="test_scraper"
        )
        
        records = list(connector.fetch())
        
        assert len(records) == 1
        assert isinstance(records[0], RawRecord)
        assert records[0].payload['name'] == "Wireless Mouse"
        assert records[0].payload['price'] == 29.99
    
    @patch.object(RobotsTxtChecker, 'is_allowed')
    def test_fetch_respects_robots_txt(self, mock_is_allowed, tenant_id, sample_urls):
        """Test that fetch respects robots.txt"""
        mock_is_allowed.return_value = False
        
        connector = WebScraperConnector(
            tenant_id=tenant_id,
            urls=sample_urls[:1],
            source_name="test_scraper"
        )
        
        records = list(connector.fetch())
        
        # Should not scrape blocked URLs
        assert len(records) == 0
        assert connector.stats['urls_blocked_robots'] == 1
    
    @patch('src.ingestion.connectors.web_scraper_connector.requests.get')
    @patch.object(RobotsTxtChecker, 'is_allowed')
    def test_fetch_handles_errors_gracefully(self, mock_is_allowed, mock_get, tenant_id, sample_urls):
        """Test that fetch continues on errors"""
        mock_is_allowed.return_value = True
        mock_get.side_effect = Exception("Network error")
        
        connector = WebScraperConnector(
            tenant_id=tenant_id,
            urls=sample_urls,
            source_name="test_scraper"
        )
        
        records = list(connector.fetch())
        
        # Should handle errors and continue
        assert len(records) == 0
        assert connector.stats['urls_failed'] == len(sample_urls)
    
    @patch('src.ingestion.connectors.web_scraper_connector.requests.get')
    @patch.object(RobotsTxtChecker, 'is_allowed')
    def test_extract_title(self, mock_is_allowed, mock_get, tenant_id, mock_html):
        """Test title extraction"""
        mock_is_allowed.return_value = True
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        connector = WebScraperConnector(
            tenant_id=tenant_id,
            urls=["https://example.com/product/1"],
            source_name="test_scraper"
        )
        
        records = list(connector.fetch())
        
        assert records[0].payload['name'] == "Wireless Mouse"
    
    @patch('src.ingestion.connectors.web_scraper_connector.requests.get')
    @patch.object(RobotsTxtChecker, 'is_allowed')
    def test_extract_price(self, mock_is_allowed, mock_get, tenant_id, mock_html):
        """Test price extraction"""
        mock_is_allowed.return_value = True
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        connector = WebScraperConnector(
            tenant_id=tenant_id,
            urls=["https://example.com/product/1"],
            source_name="test_scraper"
        )
        
        records = list(connector.fetch())
        
        assert records[0].payload['price'] == 29.99
    
    @patch('src.ingestion.connectors.web_scraper_connector.requests.get')
    @patch.object(RobotsTxtChecker, 'is_allowed')
    def test_extract_availability(self, mock_is_allowed, mock_get, tenant_id, mock_html):
        """Test availability extraction"""
        mock_is_allowed.return_value = True
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        connector = WebScraperConnector(
            tenant_id=tenant_id,
            urls=["https://example.com/product/1"],
            source_name="test_scraper"
        )
        
        records = list(connector.fetch())
        
        assert records[0].payload['availability'] == 'in_stock'
    
    @patch('src.ingestion.connectors.web_scraper_connector.requests.get')
    @patch.object(RobotsTxtChecker, 'is_allowed')
    def test_extract_rating(self, mock_is_allowed, mock_get, tenant_id, mock_html):
        """Test rating extraction"""
        mock_is_allowed.return_value = True
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        connector = WebScraperConnector(
            tenant_id=tenant_id,
            urls=["https://example.com/product/1"],
            source_name="test_scraper"
        )
        
        records = list(connector.fetch())
        
        assert records[0].payload['rating'] == 4.5
    
    def test_generate_source_id(self, tenant_id):
        """Test source ID generation"""
        connector = WebScraperConnector(
            tenant_id=tenant_id,
            urls=["https://example.com/product/123"],
            source_name="test_scraper"
        )
        
        source_id1 = connector._generate_source_id("https://example.com/product/123")
        source_id2 = connector._generate_source_id("https://example.com/product/123")
        source_id3 = connector._generate_source_id("https://example.com/product/456")
        
        # Same URL should generate same ID
        assert source_id1 == source_id2
        
        # Different URL should generate different ID
        assert source_id1 != source_id3
        
        # Should include domain prefix
        assert source_id1.startswith("EXAMPLE-")
    
    def test_get_statistics(self, tenant_id, sample_urls):
        """Test statistics tracking"""
        connector = WebScraperConnector(
            tenant_id=tenant_id,
            urls=sample_urls,
            source_name="test_scraper"
        )
        
        stats = connector.get_statistics()
        
        assert 'urls_attempted' in stats
        assert 'urls_scraped' in stats
        assert 'urls_blocked_robots' in stats
        assert 'urls_failed' in stats
