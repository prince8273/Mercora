"""Scheduled ingestion service using APScheduler"""
import logging
from typing import Optional
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from uuid import uuid4

from src.ingestion.scheduler import IngestionScheduler
from src.ingestion.marketplace_connector import MarketplaceConnector
from src.ingestion.competitor_scraper import CompetitorScraper

logger = logging.getLogger(__name__)


class ScheduledIngestionService:
    """
    Service for managing scheduled data ingestion tasks using APScheduler.
    
    Provides automated data collection from:
    - Marketplace APIs (Amazon, eBay, etc.)
    - Competitor websites (web scraping)
    - File uploads (manual ingestion)
    """
    
    def __init__(self):
        """Initialize the scheduled ingestion service"""
        self.scheduler = AsyncIOScheduler()
        self.ingestion_scheduler = IngestionScheduler()
        self.is_running = False
        
        logger.info("Initialized ScheduledIngestionService")
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule default tasks
        self._schedule_default_tasks()
        
        # Start APScheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info("Scheduled ingestion service started")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        
        logger.info("Scheduled ingestion service stopped")
    
    def _schedule_default_tasks(self):
        """Schedule default ingestion tasks"""
        
        # Task 1: Fetch marketplace data every 6 hours
        self.scheduler.add_job(
            self._fetch_marketplace_data,
            trigger=IntervalTrigger(hours=6),
            id='marketplace_data_fetch',
            name='Fetch Marketplace Data',
            replace_existing=True
        )
        logger.info("Scheduled marketplace data fetch (every 6 hours)")
        
        # Task 2: Scrape competitor prices daily at 2 AM
        self.scheduler.add_job(
            self._scrape_competitor_prices,
            trigger=CronTrigger(hour=2, minute=0),
            id='competitor_price_scrape',
            name='Scrape Competitor Prices',
            replace_existing=True
        )
        logger.info("Scheduled competitor price scraping (daily at 2 AM)")
        
        # Task 3: Health check every hour
        self.scheduler.add_job(
            self._health_check,
            trigger=IntervalTrigger(hours=1),
            id='ingestion_health_check',
            name='Ingestion Health Check',
            replace_existing=True
        )
        logger.info("Scheduled health check (every hour)")
    
    async def _fetch_marketplace_data(self):
        """Fetch data from marketplace APIs"""
        try:
            logger.info("Starting marketplace data fetch")
            
            # Use mock tenant ID for MVP
            tenant_id = uuid4()
            
            # Initialize marketplace connector
            connector = MarketplaceConnector(
                tenant_id=tenant_id,
                marketplace='amazon',
                api_key='mock_api_key'
            )
            
            # Fetch products
            products = connector.fetch_products(
                category='electronics',
                limit=100
            )
            
            logger.info(f"Fetched {len(products)} products from marketplace")
            
            # In production, would save to database here
            # For MVP, just log the result
            
        except Exception as e:
            logger.error(f"Marketplace data fetch failed: {str(e)}")
    
    async def _scrape_competitor_prices(self):
        """Scrape competitor prices"""
        try:
            logger.info("Starting competitor price scraping")
            
            # Use mock tenant ID for MVP
            tenant_id = uuid4()
            
            # Initialize scraper
            scraper = CompetitorScraper(tenant_id=tenant_id)
            
            # Mock competitor URLs
            competitor_urls = {
                'competitor1.com': [
                    'https://competitor1.com/product/123',
                    'https://competitor1.com/product/456',
                ],
                'competitor2.com': [
                    'https://competitor2.com/product/789',
                ]
            }
            
            # Scrape prices (uses mock data by default)
            results = scraper.scrape_competitor_prices(competitor_urls)
            
            logger.info(f"Scraped {len(results)} competitor products")
            
            # In production, would save to database here
            # For MVP, just log the result
            
        except Exception as e:
            logger.error(f"Competitor price scraping failed: {str(e)}")
    
    async def _health_check(self):
        """Perform health check on ingestion system"""
        try:
            logger.info("Performing ingestion health check")
            
            # Check scheduler status
            jobs = self.scheduler.get_jobs()
            logger.info(f"Active scheduled jobs: {len(jobs)}")
            
            # Check ingestion task history
            history = self.ingestion_scheduler.get_execution_history(limit=10)
            logger.info(f"Recent ingestion executions: {len(history)}")
            
            # Log any failed tasks
            failed_tasks = [h for h in history if h.get('status') == 'failed']
            if failed_tasks:
                logger.warning(f"Found {len(failed_tasks)} failed ingestion tasks")
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
    
    def add_custom_job(
        self,
        func,
        trigger_type: str = 'interval',
        job_id: Optional[str] = None,
        name: Optional[str] = None,
        **trigger_kwargs
    ):
        """
        Add a custom scheduled job.
        
        Args:
            func: Function to execute
            trigger_type: 'interval' or 'cron'
            job_id: Unique job identifier
            name: Job name
            **trigger_kwargs: Trigger-specific arguments
        """
        if trigger_type == 'interval':
            trigger = IntervalTrigger(**trigger_kwargs)
        elif trigger_type == 'cron':
            trigger = CronTrigger(**trigger_kwargs)
        else:
            raise ValueError(f"Unsupported trigger type: {trigger_type}")
        
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name,
            replace_existing=True
        )
        
        logger.info(f"Added custom job: {name or job_id}")
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {str(e)}")
    
    def get_jobs(self):
        """Get all scheduled jobs"""
        jobs = self.scheduler.get_jobs()
        return [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
            for job in jobs
        ]


# Global instance
_scheduled_service: Optional[ScheduledIngestionService] = None


def get_scheduled_service() -> ScheduledIngestionService:
    """Get or create the global scheduled service instance"""
    global _scheduled_service
    if _scheduled_service is None:
        _scheduled_service = ScheduledIngestionService()
    return _scheduled_service
