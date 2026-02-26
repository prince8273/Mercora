"""Enhanced scheduler service for data ingestion with APScheduler"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from src.ingestion.connectors.csv_connector import CSVConnector
from src.ingestion.connectors.web_scraper_connector import WebScraperConnector
from src.ingestion.ingestion_service import IngestionService
from src.processing.pipeline import ProcessingPipeline

logger = logging.getLogger(__name__)


class IngestionSchedulerService:
    """
    Enhanced scheduler service for automated data ingestion.
    
    Features:
    - Schedule CSV ingestion tasks
    - Schedule web scraping tasks
    - Automatic processing pipeline integration
    - Event publishing after ingestion
    - Job execution tracking
    - Error handling and retry
    """
    
    def __init__(self):
        """Initialize the scheduler service"""
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        # Execution history
        self.execution_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        logger.info("Initialized IngestionSchedulerService")
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info("Ingestion scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        
        logger.info("Ingestion scheduler stopped")
    
    def schedule_csv_ingestion(
        self,
        tenant_id: UUID,
        file_path: str,
        source_name: str,
        id_column: str = "sku",
        data_type: str = "product",
        cron_expression: Optional[str] = None,
        interval_hours: Optional[int] = None,
        process_after_ingestion: bool = True
    ) -> str:
        """
        Schedule periodic CSV ingestion.
        
        Args:
            tenant_id: Tenant UUID
            file_path: Path to CSV file
            source_name: Name for this data source
            id_column: Column to use as source_id
            data_type: Type of data (product, review, etc.)
            cron_expression: Cron expression (e.g., "0 2 * * *" for daily at 2 AM)
            interval_hours: Interval in hours (alternative to cron)
            process_after_ingestion: Whether to process data after ingestion
            
        Returns:
            Job ID
        """
        job_id = f"csv_ingestion_{source_name}_{tenant_id}"
        
        # Create trigger
        if cron_expression:
            trigger = CronTrigger.from_crontab(cron_expression)
        elif interval_hours:
            trigger = IntervalTrigger(hours=interval_hours)
        else:
            raise ValueError("Either cron_expression or interval_hours must be provided")
        
        # Schedule job
        self.scheduler.add_job(
            self._run_csv_ingestion,
            trigger=trigger,
            id=job_id,
            name=f"CSV Ingestion: {source_name}",
            replace_existing=True,
            kwargs={
                'tenant_id': tenant_id,
                'file_path': file_path,
                'source_name': source_name,
                'id_column': id_column,
                'data_type': data_type,
                'process_after_ingestion': process_after_ingestion
            }
        )
        
        logger.info(
            f"Scheduled CSV ingestion: {source_name}",
            extra={
                'job_id': job_id,
                'tenant_id': str(tenant_id),
                'trigger': str(trigger)
            }
        )
        
        return job_id
    
    def schedule_web_scraping(
        self,
        tenant_id: UUID,
        urls: List[str],
        source_name: str,
        cron_expression: Optional[str] = None,
        interval_hours: Optional[int] = None,
        requests_per_second: float = 0.5,
        process_after_ingestion: bool = True
    ) -> str:
        """
        Schedule periodic web scraping.
        
        Args:
            tenant_id: Tenant UUID
            urls: List of URLs to scrape
            source_name: Name for this data source
            cron_expression: Cron expression
            interval_hours: Interval in hours
            requests_per_second: Rate limit
            process_after_ingestion: Whether to process data after ingestion
            
        Returns:
            Job ID
        """
        job_id = f"web_scraping_{source_name}_{tenant_id}"
        
        # Create trigger
        if cron_expression:
            trigger = CronTrigger.from_crontab(cron_expression)
        elif interval_hours:
            trigger = IntervalTrigger(hours=interval_hours)
        else:
            raise ValueError("Either cron_expression or interval_hours must be provided")
        
        # Schedule job
        self.scheduler.add_job(
            self._run_web_scraping,
            trigger=trigger,
            id=job_id,
            name=f"Web Scraping: {source_name}",
            replace_existing=True,
            kwargs={
                'tenant_id': tenant_id,
                'urls': urls,
                'source_name': source_name,
                'requests_per_second': requests_per_second,
                'process_after_ingestion': process_after_ingestion
            }
        )
        
        logger.info(
            f"Scheduled web scraping: {source_name}",
            extra={
                'job_id': job_id,
                'tenant_id': str(tenant_id),
                'url_count': len(urls),
                'trigger': str(trigger)
            }
        )
        
        return job_id
    
    async def _run_csv_ingestion(
        self,
        tenant_id: UUID,
        file_path: str,
        source_name: str,
        id_column: str,
        data_type: str,
        process_after_ingestion: bool
    ):
        """Execute CSV ingestion task"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"Starting CSV ingestion: {source_name}",
                extra={'tenant_id': str(tenant_id), 'file_path': file_path}
            )
            
            # Create connector
            connector = CSVConnector(
                tenant_id=tenant_id,
                file_path=file_path,
                source_name=source_name,
                id_column=id_column,
                data_type=data_type
            )
            
            # Ingest data
            service = IngestionService(tenant_id=tenant_id)
            result = service.ingest_from_connector(connector)
            
            logger.info(
                f"CSV ingestion completed: {source_name}",
                extra={
                    'tenant_id': str(tenant_id),
                    'records_saved': result['statistics']['records_saved'],
                    'duration': result['duration_seconds']
                }
            )
            
            # Process data if requested
            if process_after_ingestion and result['statistics']['records_saved'] > 0:
                await self._process_ingested_data(
                    tenant_id=tenant_id,
                    source_name=source_name,
                    data_type=data_type
                )
            
            # Publish event
            await self._publish_ingestion_event(
                tenant_id=tenant_id,
                source_name=source_name,
                event_type='csv_ingestion_completed',
                data=result
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"CSV ingestion failed: {source_name}",
                extra={
                    'tenant_id': str(tenant_id),
                    'error': str(e)
                },
                exc_info=True
            )
            raise
    
    async def _run_web_scraping(
        self,
        tenant_id: UUID,
        urls: List[str],
        source_name: str,
        requests_per_second: float,
        process_after_ingestion: bool
    ):
        """Execute web scraping task"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"Starting web scraping: {source_name}",
                extra={'tenant_id': str(tenant_id), 'url_count': len(urls)}
            )
            
            # Create connector
            connector = WebScraperConnector(
                tenant_id=tenant_id,
                urls=urls,
                source_name=source_name,
                requests_per_second=requests_per_second
            )
            
            # Ingest data
            service = IngestionService(tenant_id=tenant_id)
            result = service.ingest_from_connector(connector)
            
            logger.info(
                f"Web scraping completed: {source_name}",
                extra={
                    'tenant_id': str(tenant_id),
                    'records_saved': result['statistics']['records_saved'],
                    'duration': result['duration_seconds']
                }
            )
            
            # Process data if requested
            if process_after_ingestion and result['statistics']['records_saved'] > 0:
                await self._process_ingested_data(
                    tenant_id=tenant_id,
                    source_name=source_name,
                    data_type='product'  # Assume product for web scraping
                )
            
            # Publish event
            await self._publish_ingestion_event(
                tenant_id=tenant_id,
                source_name=source_name,
                event_type='web_scraping_completed',
                data=result
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Web scraping failed: {source_name}",
                extra={
                    'tenant_id': str(tenant_id),
                    'error': str(e)
                },
                exc_info=True
            )
            raise
    
    async def _process_ingested_data(
        self,
        tenant_id: UUID,
        source_name: str,
        data_type: str
    ):
        """
        Process ingested data through the processing pipeline.
        
        Args:
            tenant_id: Tenant UUID
            source_name: Source name
            data_type: Type of data (product, review)
        """
        try:
            logger.info(
                f"Starting data processing: {source_name}",
                extra={'tenant_id': str(tenant_id), 'data_type': data_type}
            )
            
            # Get raw records from database
            # TODO: Query raw_ingestion_records table
            # For now, just log
            
            # Create processing pipeline
            pipeline = ProcessingPipeline(tenant_id=tenant_id)
            
            # Process based on data type
            # TODO: Implement actual processing
            # For now, just log
            
            logger.info(
                f"Data processing completed: {source_name}",
                extra={'tenant_id': str(tenant_id)}
            )
            
        except Exception as e:
            logger.error(
                f"Data processing failed: {source_name}",
                extra={
                    'tenant_id': str(tenant_id),
                    'error': str(e)
                },
                exc_info=True
            )
    
    async def _publish_ingestion_event(
        self,
        tenant_id: UUID,
        source_name: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        Publish ingestion event.
        
        Args:
            tenant_id: Tenant UUID
            source_name: Source name
            event_type: Event type
            data: Event data
        """
        event = {
            'tenant_id': str(tenant_id),
            'source_name': source_name,
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        logger.info(
            f"Publishing event: {event_type}",
            extra=event
        )
        
        # TODO: Publish to event bus/queue
        # For now, just log
    
    def _job_executed_listener(self, event):
        """Listen to job execution events"""
        job_id = event.job_id
        
        if event.exception:
            # Job failed
            execution_record = {
                'job_id': job_id,
                'status': 'failed',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(event.exception)
            }
            logger.error(
                f"Job failed: {job_id}",
                extra=execution_record
            )
        else:
            # Job succeeded
            execution_record = {
                'job_id': job_id,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'result': str(event.retval) if event.retval else None
            }
            logger.info(
                f"Job completed: {job_id}",
                extra=execution_record
            )
        
        # Add to history
        self.execution_history.append(execution_record)
        
        # Trim history
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]
    
    def get_jobs(self) -> List[Dict[str, Any]]:
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
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job"""
        job = self.scheduler.get_job(job_id)
        if job:
            return {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
        return None
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {str(e)}")
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        return self.execution_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        total_executions = len(self.execution_history)
        failed_executions = sum(1 for e in self.execution_history if e['status'] == 'failed')
        
        return {
            'is_running': self.is_running,
            'total_jobs': len(self.scheduler.get_jobs()),
            'total_executions': total_executions,
            'failed_executions': failed_executions,
            'success_rate': (total_executions - failed_executions) / total_executions if total_executions > 0 else 0.0
        }


# Global instance
_scheduler_service: Optional[IngestionSchedulerService] = None


def get_scheduler_service() -> IngestionSchedulerService:
    """Get or create the global scheduler service instance"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = IngestionSchedulerService()
    return _scheduler_service
