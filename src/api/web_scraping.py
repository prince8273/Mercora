"""Web scraping API endpoints for direct URL input"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, HttpUrl, Field
from uuid import uuid4, UUID

from src.database import get_db
from src.ingestion.competitor_scraper import CompetitorScraper, ScrapedData
from src.models.product import Product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraping", tags=["web-scraping"])


class ScrapeRequest(BaseModel):
    """Request to scrape a single URL"""
    url: HttpUrl = Field(..., description="URL to scrape")
    use_real_scraping: bool = Field(True, description="Use real web scraping (True) or mock data (False)")
    save_to_database: bool = Field(True, description="Save scraped data to database")


class BulkScrapeRequest(BaseModel):
    """Request to scrape multiple URLs"""
    urls: List[HttpUrl] = Field(..., description="List of URLs to scrape", min_items=1, max_items=100)
    use_real_scraping: bool = Field(True, description="Use real web scraping (True) or mock data (False)")
    save_to_database: bool = Field(True, description="Save scraped data to database")


class ScrapeResponse(BaseModel):
    """Response from scraping operation"""
    job_id: str
    status: str
    message: str
    urls_count: int
    scraped_data: Optional[List[dict]] = None


class ScrapeStatusResponse(BaseModel):
    """Status of a scraping job"""
    job_id: str
    status: str
    urls_total: int
    urls_scraped: int
    urls_failed: int
    products_saved: int
    errors: List[str]
    started_at: datetime
    completed_at: Optional[datetime] = None


# In-memory job tracking (in production, use database or Redis)
scraping_jobs: dict = {}


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_single_url(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Scrape a single URL and extract product data.
    
    This endpoint:
    - Accepts any product page URL
    - Respects robots.txt
    - Applies rate limiting
    - Extracts product information (title, price, description, images)
    - Optionally saves to database
    
    Example URLs:
    - Amazon: https://www.amazon.com/dp/B08N5WRWNW
    - eBay: https://www.ebay.com/itm/123456789
    - Any e-commerce site with product pages
    """
    job_id = str(uuid4())
    tenant_id = uuid4()  # In production, get from authenticated user
    
    # Create scraper
    scraper = CompetitorScraper(tenant_id=tenant_id)
    
    # Create job record
    scraping_jobs[job_id] = {
        'job_id': job_id,
        'status': 'processing',
        'urls_total': 1,
        'urls_scraped': 0,
        'urls_failed': 0,
        'products_saved': 0,
        'errors': [],
        'started_at': datetime.utcnow(),
        'completed_at': None
    }
    
    # Process in background
    background_tasks.add_task(
        _process_single_scrape,
        job_id,
        str(request.url),
        request.use_real_scraping,
        request.save_to_database,
        scraper,
        db
    )
    
    return ScrapeResponse(
        job_id=job_id,
        status="processing",
        message=f"Scraping {request.url}",
        urls_count=1
    )


@router.post("/scrape/bulk", response_model=ScrapeResponse)
async def scrape_multiple_urls(
    request: BulkScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Scrape multiple URLs in bulk.
    
    This endpoint:
    - Accepts up to 100 URLs at once
    - Processes them with rate limiting
    - Respects robots.txt for each domain
    - Extracts product information from all URLs
    - Optionally saves all to database
    
    Perfect for:
    - Competitor price monitoring
    - Product catalog updates
    - Market research
    """
    job_id = str(uuid4())
    tenant_id = uuid4()  # In production, get from authenticated user
    
    urls = [str(url) for url in request.urls]
    
    # Create scraper
    scraper = CompetitorScraper(tenant_id=tenant_id)
    
    # Create job record
    scraping_jobs[job_id] = {
        'job_id': job_id,
        'status': 'processing',
        'urls_total': len(urls),
        'urls_scraped': 0,
        'urls_failed': 0,
        'products_saved': 0,
        'errors': [],
        'started_at': datetime.utcnow(),
        'completed_at': None
    }
    
    # Process in background
    background_tasks.add_task(
        _process_bulk_scrape,
        job_id,
        urls,
        request.use_real_scraping,
        request.save_to_database,
        scraper,
        db
    )
    
    return ScrapeResponse(
        job_id=job_id,
        status="processing",
        message=f"Scraping {len(urls)} URLs",
        urls_count=len(urls)
    )


@router.get("/status/{job_id}", response_model=ScrapeStatusResponse)
async def get_scraping_status(job_id: str):
    """Get status of a scraping job"""
    if job_id not in scraping_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = scraping_jobs[job_id]
    
    return ScrapeStatusResponse(
        job_id=job['job_id'],
        status=job['status'],
        urls_total=job['urls_total'],
        urls_scraped=job['urls_scraped'],
        urls_failed=job['urls_failed'],
        products_saved=job['products_saved'],
        errors=job['errors'],
        started_at=job['started_at'],
        completed_at=job['completed_at']
    )


@router.get("/jobs")
async def list_scraping_jobs(limit: int = 50):
    """List recent scraping jobs"""
    jobs = list(scraping_jobs.values())
    jobs.sort(key=lambda x: x['started_at'], reverse=True)
    return {
        "total": len(jobs),
        "jobs": jobs[:limit]
    }


@router.get("/rate-limits")
async def get_rate_limits():
    """
    Get current rate limiting status for all domains.
    
    Shows which domains can be scraped immediately and which need to wait.
    """
    tenant_id = uuid4()  # In production, get from authenticated user
    scraper = CompetitorScraper(tenant_id=tenant_id)
    
    status = scraper.get_rate_limit_status()
    
    return {
        "domains": status,
        "rate_limit": "1 request per 2 seconds per domain"
    }


async def _process_single_scrape(
    job_id: str,
    url: str,
    use_real_scraping: bool,
    save_to_database: bool,
    scraper: CompetitorScraper,
    db: AsyncSession
):
    """Process a single URL scraping job"""
    try:
        logger.info(f"Job {job_id}: Scraping {url}")
        
        # Scrape the URL
        scraped_data = scraper.scrape_product_page(url, use_real_scraping=use_real_scraping)
        
        if not scraped_data:
            scraping_jobs[job_id].update({
                'status': 'failed',
                'urls_failed': 1,
                'errors': ['Failed to scrape URL - may be blocked by robots.txt'],
                'completed_at': datetime.utcnow()
            })
            return
        
        # Save to database if requested
        products_saved = 0
        if save_to_database:
            try:
                product = Product(
                    sku=scraped_data.data.get('sku'),
                    name=scraped_data.data.get('name'),
                    price=scraped_data.data.get('price', 0.0),
                    currency=scraped_data.data.get('currency', 'USD'),
                    marketplace=scraped_data.data.get('marketplace'),
                    category=scraped_data.data.get('category', 'Uncategorized'),
                    inventory_level=scraped_data.data.get('inventory_level', 0)
                )
                db.add(product)
                await db.commit()
                products_saved = 1
                logger.info(f"Job {job_id}: Saved product {product.sku} to database")
            except Exception as e:
                logger.error(f"Job {job_id}: Failed to save to database: {str(e)}")
                scraping_jobs[job_id]['errors'].append(f"Database save failed: {str(e)}")
        
        # Update job status
        scraping_jobs[job_id].update({
            'status': 'completed',
            'urls_scraped': 1,
            'products_saved': products_saved,
            'completed_at': datetime.utcnow()
        })
        
        logger.info(f"Job {job_id}: Completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id}: Failed with error: {str(e)}")
        scraping_jobs[job_id].update({
            'status': 'failed',
            'urls_failed': 1,
            'errors': [str(e)],
            'completed_at': datetime.utcnow()
        })


async def _process_bulk_scrape(
    job_id: str,
    urls: List[str],
    use_real_scraping: bool,
    save_to_database: bool,
    scraper: CompetitorScraper,
    db: AsyncSession
):
    """Process multiple URLs scraping job"""
    try:
        logger.info(f"Job {job_id}: Scraping {len(urls)} URLs")
        
        scraped_count = 0
        failed_count = 0
        products_saved = 0
        errors = []
        
        for url in urls:
            try:
                # Scrape the URL
                scraped_data = scraper.scrape_product_page(url, use_real_scraping=use_real_scraping)
                
                if not scraped_data:
                    failed_count += 1
                    errors.append(f"{url}: Failed to scrape (robots.txt or error)")
                    continue
                
                scraped_count += 1
                
                # Save to database if requested
                if save_to_database:
                    try:
                        product = Product(
                            sku=scraped_data.data.get('sku'),
                            name=scraped_data.data.get('name'),
                            price=scraped_data.data.get('price', 0.0),
                            currency=scraped_data.data.get('currency', 'USD'),
                            marketplace=scraped_data.data.get('marketplace'),
                            category=scraped_data.data.get('category', 'Uncategorized'),
                            inventory_level=scraped_data.data.get('inventory_level', 0)
                        )
                        db.add(product)
                        await db.commit()
                        products_saved += 1
                    except Exception as e:
                        logger.error(f"Failed to save product from {url}: {str(e)}")
                        errors.append(f"{url}: Database save failed - {str(e)}")
                
                # Update progress
                scraping_jobs[job_id].update({
                    'urls_scraped': scraped_count,
                    'urls_failed': failed_count,
                    'products_saved': products_saved,
                    'errors': errors
                })
                
            except Exception as e:
                failed_count += 1
                errors.append(f"{url}: {str(e)}")
                logger.error(f"Failed to scrape {url}: {str(e)}")
        
        # Update final job status
        scraping_jobs[job_id].update({
            'status': 'completed',
            'urls_scraped': scraped_count,
            'urls_failed': failed_count,
            'products_saved': products_saved,
            'errors': errors,
            'completed_at': datetime.utcnow()
        })
        
        logger.info(f"Job {job_id}: Completed - {scraped_count} scraped, {failed_count} failed, {products_saved} saved")
        
    except Exception as e:
        logger.error(f"Job {job_id}: Failed with error: {str(e)}")
        scraping_jobs[job_id].update({
            'status': 'failed',
            'errors': [str(e)],
            'completed_at': datetime.utcnow()
        })
