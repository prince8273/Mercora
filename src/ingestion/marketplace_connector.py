"""Marketplace API connector for data ingestion"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
import time
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class RawDataRecord:
    """Raw data record with metadata"""
    source: str
    data_type: str  # 'product', 'sales', 'inventory', 'review'
    data: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any]


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, calls_per_second: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_second: Maximum calls allowed per second
        """
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0.0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.min_interval:
            sleep_time = self.min_interval - time_since_last_call
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()


class MarketplaceConnector:
    """
    Connects to marketplace APIs to fetch product, sales, and inventory data.
    
    In production, this would integrate with real marketplace APIs (Amazon MWS, eBay API, etc.).
    For MVP, provides mock data generation with proper structure.
    
    Responsibilities:
    - API authentication and credential management
    - Fetch products, sales data, and inventory
    - Rate limiting and retry with exponential backoff
    - Store raw data with timestamp and source metadata
    """
    
    def __init__(self, tenant_id: UUID, marketplace: str, credentials: Optional[Dict[str, str]] = None):
        """
        Initialize marketplace connector.
        
        Args:
            tenant_id: Tenant UUID
            marketplace: Marketplace name (amazon, ebay, walmart, shopify)
            credentials: API credentials dictionary
        """
        self.tenant_id = tenant_id
        self.marketplace = marketplace
        self.credentials = credentials or {}
        self.rate_limiter = RateLimiter(calls_per_second=2.0)  # 2 calls per second
        self.max_retries = 3
        self.base_retry_delay = 1.0  # seconds
    
    def authenticate(self) -> bool:
        """
        Authenticate with marketplace API.
        
        Returns:
            True if authentication successful
        """
        # In production, this would perform actual OAuth or API key validation
        logger.info(f"Authenticating with {self.marketplace} API")
        
        if not self.credentials:
            logger.warning(f"No credentials provided for {self.marketplace}")
            return False
        
        # Mock authentication
        required_keys = ['api_key', 'api_secret']
        has_required = all(key in self.credentials for key in required_keys)
        
        if has_required:
            logger.info(f"Successfully authenticated with {self.marketplace}")
            return True
        else:
            logger.error(f"Missing required credentials for {self.marketplace}")
            return False
    
    def fetch_products(self, limit: int = 100, offset: int = 0) -> List[RawDataRecord]:
        """
        Fetch product catalog from marketplace.
        
        Args:
            limit: Maximum number of products to fetch
            offset: Pagination offset
            
        Returns:
            List of raw product records
        """
        logger.info(f"Fetching products from {self.marketplace} (limit={limit}, offset={offset})")
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        # In production, this would call actual API
        # For MVP, generate mock data
        records = []
        timestamp = datetime.utcnow()
        
        for i in range(limit):
            product_data = {
                'sku': f"{self.marketplace.upper()}-{offset + i + 1:05d}",
                'name': f"Product {offset + i + 1} from {self.marketplace}",
                'price': 10.0 + (i * 5.0),
                'currency': 'USD',
                'marketplace': self.marketplace,
                'category': 'Electronics' if i % 2 == 0 else 'Books',
                'inventory_level': 100 - (i * 2),
                'tenant_id': str(self.tenant_id)
            }
            
            record = RawDataRecord(
                source=self.marketplace,
                data_type='product',
                data=product_data,
                timestamp=timestamp,
                metadata={
                    'api_version': '1.0',
                    'fetch_method': 'api',
                    'pagination': {'limit': limit, 'offset': offset}
                }
            )
            records.append(record)
        
        logger.info(f"Fetched {len(records)} products from {self.marketplace}")
        return records
    
    def fetch_sales_data(self, start_date: datetime, end_date: datetime) -> List[RawDataRecord]:
        """
        Fetch sales data from marketplace.
        
        Args:
            start_date: Start date for sales data
            end_date: End date for sales data
            
        Returns:
            List of raw sales records
        """
        logger.info(f"Fetching sales data from {self.marketplace} ({start_date} to {end_date})")
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Mock sales data
        records = []
        timestamp = datetime.utcnow()
        
        # Generate 10 mock sales records
        for i in range(10):
            sales_data = {
                'order_id': f"ORD-{self.marketplace.upper()}-{i+1:06d}",
                'sku': f"{self.marketplace.upper()}-{i+1:05d}",
                'quantity': i + 1,
                'unit_price': 10.0 + (i * 5.0),
                'total_amount': (10.0 + (i * 5.0)) * (i + 1),
                'sale_date': start_date,
                'marketplace': self.marketplace,
                'tenant_id': str(self.tenant_id)
            }
            
            record = RawDataRecord(
                source=self.marketplace,
                data_type='sales',
                data=sales_data,
                timestamp=timestamp,
                metadata={
                    'api_version': '1.0',
                    'date_range': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                }
            )
            records.append(record)
        
        logger.info(f"Fetched {len(records)} sales records from {self.marketplace}")
        return records
    
    def fetch_inventory(self) -> List[RawDataRecord]:
        """
        Fetch current inventory levels from marketplace.
        
        Returns:
            List of raw inventory records
        """
        logger.info(f"Fetching inventory from {self.marketplace}")
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Mock inventory data
        records = []
        timestamp = datetime.utcnow()
        
        for i in range(20):
            inventory_data = {
                'sku': f"{self.marketplace.upper()}-{i+1:05d}",
                'available_quantity': 100 - (i * 3),
                'reserved_quantity': i * 2,
                'warehouse_location': f"WH-{i % 3 + 1}",
                'last_updated': timestamp.isoformat(),
                'marketplace': self.marketplace,
                'tenant_id': str(self.tenant_id)
            }
            
            record = RawDataRecord(
                source=self.marketplace,
                data_type='inventory',
                data=inventory_data,
                timestamp=timestamp,
                metadata={
                    'api_version': '1.0',
                    'fetch_method': 'api'
                }
            )
            records.append(record)
        
        logger.info(f"Fetched {len(records)} inventory records from {self.marketplace}")
        return records
    
    def fetch_with_retry(self, fetch_func: callable, *args, **kwargs) -> List[RawDataRecord]:
        """
        Execute fetch function with exponential backoff retry.
        
        Args:
            fetch_func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            List of raw data records
            
        Raises:
            Exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return fetch_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff delay
                    delay = self.base_retry_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
        
        raise last_exception
