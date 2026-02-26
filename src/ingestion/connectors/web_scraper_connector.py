"""Web scraper connector for competitor data ingestion"""
import logging
import time
import random
from datetime import datetime
from typing import Iterator, Optional, Dict, Any, List
from uuid import UUID
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from src.ingestion.base import BaseConnector, RawRecord

logger = logging.getLogger(__name__)


class RobotsTxtChecker:
    """Checks and caches robots.txt rules per domain"""
    
    def __init__(self, user_agent: str):
        """
        Initialize robots.txt checker.
        
        Args:
            user_agent: User agent string to check against
        """
        self.user_agent = user_agent
        self.parsers: Dict[str, RobotFileParser] = {}
        self.cache_timeout = 3600  # 1 hour
        self.last_checked: Dict[str, float] = {}
    
    def is_allowed(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed, False otherwise
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Check cache
        if domain in self.parsers:
            # Check if cache is still valid
            if time.time() - self.last_checked.get(domain, 0) < self.cache_timeout:
                parser = self.parsers[domain]
                return parser.can_fetch(self.user_agent, url)
        
        # Fetch and parse robots.txt
        try:
            robots_url = f"{parsed.scheme}://{domain}/robots.txt"
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.read()
            
            self.parsers[domain] = parser
            self.last_checked[domain] = time.time()
            
            allowed = parser.can_fetch(self.user_agent, url)
            
            logger.info(
                f"Robots.txt check for {domain}",
                extra={
                    'domain': domain,
                    'url': url,
                    'allowed': allowed
                }
            )
            
            return allowed
            
        except Exception as e:
            logger.warning(
                f"Failed to fetch robots.txt for {domain}: {str(e)}. Assuming allowed.",
                extra={'domain': domain, 'error': str(e)}
            )
            # If we can't fetch robots.txt, assume allowed (be conservative)
            return True
    
    def get_crawl_delay(self, url: str) -> Optional[float]:
        """
        Get crawl delay from robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            Crawl delay in seconds, or None if not specified
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if domain in self.parsers:
            parser = self.parsers[domain]
            delay = parser.crawl_delay(self.user_agent)
            return float(delay) if delay else None
        
        return None


class DomainRateLimiter:
    """Token bucket rate limiter per domain"""
    
    def __init__(self, requests_per_second: float = 0.5):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second per domain
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_times: Dict[str, float] = {}
    
    def wait_if_needed(self, domain: str, crawl_delay: Optional[float] = None):
        """
        Wait if necessary to respect rate limit.
        
        Args:
            domain: Domain name
            crawl_delay: Optional crawl delay from robots.txt
        """
        # Use crawl delay if specified, otherwise use configured rate
        delay = crawl_delay if crawl_delay else self.min_interval
        
        current_time = time.time()
        last_time = self.last_request_times.get(domain, 0.0)
        time_since_last = current_time - last_time
        
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            # Add jitter (±10%)
            jitter = sleep_time * 0.1 * (2 * random.random() - 1)
            sleep_time = max(0, sleep_time + jitter)
            
            logger.debug(
                f"Rate limiting {domain}: sleeping for {sleep_time:.2f}s",
                extra={'domain': domain, 'sleep_time': sleep_time}
            )
            time.sleep(sleep_time)
        
        self.last_request_times[domain] = time.time()


class WebScraperConnector(BaseConnector):
    """
    Web scraper connector for ingesting competitor data.
    
    Features:
    - Respects robots.txt
    - Per-domain rate limiting with jitter
    - Retry with exponential backoff
    - Generic product extraction
    - Structured error handling
    """
    
    def __init__(
        self,
        tenant_id: UUID,
        urls: List[str],
        source_name: str = "web_scraper",
        user_agent: Optional[str] = None,
        requests_per_second: float = 0.5,
        timeout: int = 10
    ):
        """
        Initialize web scraper connector.
        
        Args:
            tenant_id: Tenant UUID
            urls: List of URLs to scrape
            source_name: Name for this data source
            user_agent: Custom user agent string
            requests_per_second: Max requests per second per domain
            timeout: Request timeout in seconds
        """
        super().__init__(tenant_id, source_name)
        self.urls = urls
        self.user_agent = user_agent or "EcommerceIntelligenceBot/1.0 (+https://example.com/bot)"
        self.timeout = timeout
        
        # Initialize components
        self.robots_checker = RobotsTxtChecker(self.user_agent)
        self.rate_limiter = DomainRateLimiter(requests_per_second)
        
        # Statistics
        self.stats = {
            'urls_attempted': 0,
            'urls_scraped': 0,
            'urls_blocked_robots': 0,
            'urls_failed': 0
        }
        
        logger.info(
            "Initialized web scraper connector",
            extra={
                'tenant_id': str(tenant_id),
                'source_name': source_name,
                'url_count': len(urls),
                'user_agent': self.user_agent
            }
        )
    
    def fetch(self, *, since: Optional[datetime] = None) -> Iterator[RawRecord]:
        """
        Fetch records by scraping URLs.
        
        Args:
            since: Not used for web scraping (always fetches all URLs)
            
        Yields:
            RawRecord objects
        """
        logger.info(
            f"Starting web scraping from {len(self.urls)} URLs",
            extra={
                'tenant_id': str(self.tenant_id),
                'source_name': self.source_name,
                'url_count': len(self.urls)
            }
        )
        
        for url in self.urls:
            self.stats['urls_attempted'] += 1
            
            try:
                # Check robots.txt
                if not self.robots_checker.is_allowed(url):
                    logger.warning(
                        f"URL blocked by robots.txt: {url}",
                        extra={'url': url}
                    )
                    self.stats['urls_blocked_robots'] += 1
                    continue
                
                # Get crawl delay
                crawl_delay = self.robots_checker.get_crawl_delay(url)
                
                # Rate limiting
                parsed = urlparse(url)
                self.rate_limiter.wait_if_needed(parsed.netloc, crawl_delay)
                
                # Scrape with retry
                product_data = self._scrape_with_retry(url)
                
                if product_data:
                    # Create source_id from URL
                    source_id = self._generate_source_id(url)
                    
                    # Create metadata
                    metadata = {
                        'url': url,
                        'domain': parsed.netloc,
                        'scrape_method': 'html_parse',
                        'user_agent': self.user_agent
                    }
                    
                    # Yield record
                    record = RawRecord(
                        source_id=source_id,
                        payload=product_data,
                        retrieved_at=datetime.utcnow(),
                        metadata=metadata
                    )
                    
                    yield record
                    self.stats['urls_scraped'] += 1
                
            except Exception as e:
                logger.error(
                    f"Failed to scrape {url}: {str(e)}",
                    extra={'url': url, 'error': str(e)}
                )
                self.stats['urls_failed'] += 1
                continue
        
        logger.info(
            f"Web scraping completed",
            extra={
                'tenant_id': str(self.tenant_id),
                'source_name': self.source_name,
                **self.stats
            }
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, requests.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _scrape_with_retry(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape URL with retry logic.
        
        Args:
            url: URL to scrape
            
        Returns:
            Product data dictionary or None
        """
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'DNT': '1'
        }
        
        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract product data
        product_data = self._extract_product_data(soup, url)
        
        logger.info(
            f"Successfully scraped: {url}",
            extra={'url': url, 'status_code': response.status_code}
        )
        
        return product_data
    
    def _extract_product_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract product data from HTML.
        
        Uses generic selectors that work across many e-commerce sites.
        
        Args:
            soup: BeautifulSoup object
            url: Product URL
            
        Returns:
            Product data dictionary
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract price
        price = self._extract_price(soup)
        
        # Extract description
        description = self._extract_description(soup)
        
        # Extract images
        images = self._extract_images(soup)
        
        # Extract availability
        availability = self._extract_availability(soup)
        
        # Extract rating
        rating = self._extract_rating(soup)
        
        return {
            'url': url,
            'sku': self._generate_source_id(url),
            'name': title or f"Product from {domain}",
            'price': price,
            'currency': 'USD',  # TODO: Extract currency
            'marketplace': domain,
            'availability': availability,
            'description': description or '',
            'images': images,
            'rating': rating,
            'scraped_at': datetime.utcnow().isoformat()
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product title"""
        selectors = [
            'h1',
            '.product-title',
            '#product-title',
            '[itemprop="name"]',
            '.product-name',
            'h1.title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract product price"""
        import re
        
        selectors = [
            '.price',
            '.product-price',
            '[itemprop="price"]',
            '.a-price-whole',
            'span.price',
            '.price-current'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract numeric value
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    try:
                        return float(price_match.group())
                    except ValueError:
                        continue
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product description"""
        selectors = [
            '.product-description',
            '#product-description',
            '[itemprop="description"]',
            '.description',
            '#description'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)[:500]  # Limit length
        
        return None
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract product images"""
        images = []
        
        # Try various image selectors
        img_elements = soup.select('img[src*="product"], img[data-src*="product"], .product-image img')
        
        for img in img_elements[:5]:  # Limit to 5 images
            img_url = img.get('src') or img.get('data-src')
            if img_url:
                # Make absolute URL if relative
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    parsed = urlparse(soup.find('base', href=True).get('href') if soup.find('base', href=True) else '')
                    img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                
                images.append(img_url)
        
        return images
    
    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract product availability"""
        # Look for common availability indicators
        availability_texts = [
            'in stock',
            'available',
            'add to cart',
            'buy now'
        ]
        
        page_text = soup.get_text().lower()
        
        for text in availability_texts:
            if text in page_text:
                return 'in_stock'
        
        # Check for out of stock indicators
        out_of_stock_texts = [
            'out of stock',
            'unavailable',
            'sold out',
            'not available'
        ]
        
        for text in out_of_stock_texts:
            if text in page_text:
                return 'out_of_stock'
        
        return 'unknown'
    
    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract product rating"""
        import re
        
        selectors = [
            '[itemprop="ratingValue"]',
            '.rating',
            '.star-rating',
            '.product-rating'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                rating_text = element.get_text(strip=True)
                # Extract numeric value
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        return float(rating_match.group(1))
                    except ValueError:
                        continue
        
        return None
    
    def _generate_source_id(self, url: str) -> str:
        """
        Generate unique source ID from URL.
        
        Args:
            url: Product URL
            
        Returns:
            Source ID string
        """
        import hashlib
        
        # Use URL hash as source ID
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        parsed = urlparse(url)
        domain_short = parsed.netloc.split('.')[0].upper()
        
        return f"{domain_short}-{url_hash}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return self.stats.copy()
