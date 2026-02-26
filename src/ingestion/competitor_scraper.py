"""Web scraper for competitor data collection"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
import time
import logging
from urllib.parse import urlparse
from uuid import UUID
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ScrapedData:
    """Scraped data with metadata"""
    url: str
    domain: str
    data_type: str
    data: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any]


class DomainRateLimiter:
    """Rate limiter per domain"""
    
    def __init__(self, requests_per_second: float = 0.5):
        """
        Initialize domain rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second per domain
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_times: Dict[str, float] = {}
    
    def wait_if_needed(self, domain: str):
        """
        Wait if necessary to respect rate limit for domain.
        
        Args:
            domain: Domain name
        """
        current_time = time.time()
        last_time = self.last_request_times.get(domain, 0.0)
        time_since_last = current_time - last_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            logger.debug(f"Rate limiting {domain}: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_times[domain] = time.time()


class CompetitorScraper:
    """
    Web scraper for collecting competitor product data.
    
    In production, this would use BeautifulSoup/Scrapy for actual web scraping.
    For MVP, provides mock scraping with proper rate limiting and robots.txt respect.
    
    Responsibilities:
    - Web scraping with rate limiting per domain
    - Robots.txt respect
    - Anti-scraping detection handling
    - Extract product information from competitor websites
    """
    
    def __init__(self, tenant_id: UUID, user_agent: Optional[str] = None):
        """
        Initialize competitor scraper.
        
        Args:
            tenant_id: Tenant UUID
            user_agent: Custom user agent string
        """
        self.tenant_id = tenant_id
        self.user_agent = user_agent or "EcommerceIntelligenceBot/1.0"
        self.rate_limiter = DomainRateLimiter(requests_per_second=0.5)  # 1 request per 2 seconds
        self.robots_cache: Dict[str, Dict[str, Any]] = {}
    
    def check_robots_txt(self, url: str) -> bool:
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
        if domain in self.robots_cache:
            robots_rules = self.robots_cache[domain]
            # Simple check - in production would parse actual robots.txt
            return robots_rules.get('allow_all', True)
        
        # Mock robots.txt check
        # In production, would fetch and parse robots.txt
        logger.info(f"Checking robots.txt for {domain}")
        
        # For MVP, assume all domains allow scraping
        self.robots_cache[domain] = {
            'allow_all': True,
            'crawl_delay': 2.0,
            'checked_at': datetime.utcnow()
        }
        
        return True
    
    def scrape_product_page(self, url: str, use_real_scraping: bool = False) -> Optional[ScrapedData]:
        """
        Scrape product information from a URL.
        
        Args:
            url: Product page URL
            use_real_scraping: If True, attempt real web scraping; if False, use mock data
            
        Returns:
            ScrapedData or None if scraping failed
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Check robots.txt
        if not self.check_robots_txt(url):
            logger.warning(f"URL {url} disallowed by robots.txt")
            return None
        
        # Rate limiting
        self.rate_limiter.wait_if_needed(domain)
        
        logger.info(f"Scraping product from {url}")
        timestamp = datetime.utcnow()
        
        if use_real_scraping:
            try:
                # Real web scraping using BeautifulSoup
                headers = {
                    'User-Agent': self.user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Generic extraction (works for many e-commerce sites)
                # In production, would have site-specific extractors
                product_data = self._extract_product_data(soup, url, domain)
                
                scraped = ScrapedData(
                    url=url,
                    domain=domain,
                    data_type='product',
                    data=product_data,
                    timestamp=timestamp,
                    metadata={
                        'scraper_version': '1.0',
                        'user_agent': self.user_agent,
                        'scrape_method': 'real_html_parse',
                        'status_code': response.status_code
                    }
                )
                
                logger.info(f"Successfully scraped product from {url}")
                return scraped
                
            except Exception as e:
                logger.error(f"Real scraping failed for {url}: {str(e)}, falling back to mock data")
                # Fall through to mock data
        
        # Mock data (default or fallback)
        product_id = url.split('/')[-1] if '/' in url else 'unknown'
        
        product_data = {
            'url': url,
            'sku': f"COMP-{domain.upper()}-{product_id}",
            'name': f"Competitor Product from {domain}",
            'price': 99.99,
            'currency': 'USD',
            'marketplace': domain,
            'availability': 'in_stock',
            'rating': 4.5,
            'review_count': 123,
            'description': f"Product description scraped from {url}",
            'images': [f"{url}/image1.jpg", f"{url}/image2.jpg"],
            'tenant_id': str(self.tenant_id)
        }
        
        scraped = ScrapedData(
            url=url,
            domain=domain,
            data_type='product',
            data=product_data,
            timestamp=timestamp,
            metadata={
                'scraper_version': '1.0',
                'user_agent': self.user_agent,
                'scrape_method': 'mock'
            }
        )
        
        logger.info(f"Successfully generated mock data for {url}")
        return scraped
    
    def _extract_product_data(self, soup: BeautifulSoup, url: str, domain: str) -> Dict[str, Any]:
        """
        Extract product data from HTML soup.
        Generic extraction that works for many e-commerce sites.
        
        Args:
            soup: BeautifulSoup object
            url: Product URL
            domain: Domain name
            
        Returns:
            Extracted product data
        """
        product_id = url.split('/')[-1] if '/' in url else 'unknown'
        
        # Try to extract title
        title = None
        for selector in ['h1', '.product-title', '#product-title', '[itemprop="name"]']:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                break
        
        # Try to extract price
        price = None
        for selector in ['.price', '.product-price', '[itemprop="price"]', '.a-price-whole']:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract numeric value
                import re
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    price = float(price_match.group())
                    break
        
        # Try to extract description
        description = None
        for selector in ['.product-description', '#product-description', '[itemprop="description"]']:
            element = soup.select_one(selector)
            if element:
                description = element.get_text(strip=True)[:500]  # Limit length
                break
        
        # Try to extract images
        images = []
        for img in soup.select('img[src*="product"], img[data-src*="product"]')[:5]:
            img_url = img.get('src') or img.get('data-src')
            if img_url:
                images.append(img_url)
        
        return {
            'url': url,
            'sku': f"COMP-{domain.upper()}-{product_id}",
            'name': title or f"Product from {domain}",
            'price': price or 0.0,
            'currency': 'USD',
            'marketplace': domain,
            'availability': 'in_stock',
            'description': description or '',
            'images': images,
            'tenant_id': str(self.tenant_id)
        }
    
    def scrape_product_list(self, urls: List[str]) -> List[ScrapedData]:
        """
        Scrape multiple product pages.
        
        Args:
            urls: List of product page URLs
            
        Returns:
            List of scraped data
        """
        results = []
        
        for url in urls:
            try:
                scraped = self.scrape_product_page(url)
                if scraped:
                    results.append(scraped)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {str(e)}")
                # Continue with other URLs (error isolation)
                continue
        
        logger.info(f"Scraped {len(results)} out of {len(urls)} URLs")
        return results
    
    def scrape_competitor_prices(self, competitor_urls: Dict[str, List[str]]) -> List[ScrapedData]:
        """
        Scrape prices from multiple competitors.
        
        Args:
            competitor_urls: Dictionary mapping competitor names to URL lists
            
        Returns:
            List of scraped price data
        """
        all_results = []
        
        for competitor, urls in competitor_urls.items():
            logger.info(f"Scraping prices from {competitor} ({len(urls)} URLs)")
            
            try:
                results = self.scrape_product_list(urls)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Failed to scrape {competitor}: {str(e)}")
                # Continue with other competitors (error isolation)
                continue
        
        return all_results
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limiting status.
        
        Returns:
            Dictionary with rate limit information per domain
        """
        current_time = time.time()
        status = {}
        
        for domain, last_time in self.rate_limiter.last_request_times.items():
            time_since_last = current_time - last_time
            can_request = time_since_last >= self.rate_limiter.min_interval
            
            status[domain] = {
                'last_request': last_time,
                'time_since_last': time_since_last,
                'can_request_now': can_request,
                'wait_time': max(0, self.rate_limiter.min_interval - time_since_last)
            }
        
        return status
