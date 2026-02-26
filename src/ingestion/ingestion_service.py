"""Ingestion service for saving raw records to database"""
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.ingestion.base import BaseConnector, RawRecord
from src.models.raw_ingestion_record import RawIngestionRecord
from src.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service for ingesting data from connectors and saving to database.
    
    Responsibilities:
    - Fetch records from connectors
    - Save to raw_ingestion_records table
    - Handle duplicates (idempotency)
    - Track ingestion statistics
    - Structured logging
    """
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize ingestion service.
        
        Args:
            tenant_id: Tenant UUID
        """
        self.tenant_id = tenant_id
        self.stats = {
            'records_fetched': 0,
            'records_saved': 0,
            'records_skipped_duplicate': 0,
            'records_failed': 0
        }
    
    def ingest_from_connector(
        self,
        connector: BaseConnector,
        since: Optional[datetime] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Ingest data from a connector and save to database.
        
        Args:
            connector: Connector instance to fetch from
            since: Only fetch records after this timestamp
            batch_size: Number of records to commit at once
            
        Returns:
            Dictionary with ingestion statistics
        """
        # Run async ingestion in event loop
        return asyncio.run(self._ingest_async(connector, since, batch_size))
    
    async def _ingest_async(
        self,
        connector: BaseConnector,
        since: Optional[datetime],
        batch_size: int
    ) -> Dict[str, Any]:
        """Async implementation of ingestion"""
        start_time = datetime.utcnow()
        
        logger.info(
            f"Starting ingestion from {connector.source_name}",
            extra={
                'tenant_id': str(self.tenant_id),
                'source_name': connector.source_name,
                'since': since.isoformat() if since else None
            }
        )
        
        # Reset stats
        self.stats = {
            'records_fetched': 0,
            'records_saved': 0,
            'records_skipped_duplicate': 0,
            'records_failed': 0
        }
        
        async with AsyncSessionLocal() as db:
            batch = []
            
            try:
                # Fetch records from connector
                for raw_record in connector.fetch(since=since):
                    self.stats['records_fetched'] += 1
                    
                    # Convert to database model
                    db_record = self._create_db_record(
                        raw_record=raw_record,
                        source_name=connector.source_name
                    )
                    
                    batch.append(db_record)
                    
                    # Commit batch
                    if len(batch) >= batch_size:
                        await self._save_batch(db, batch)
                        batch = []
                
                # Commit remaining records
                if batch:
                    await self._save_batch(db, batch)
                
                # Calculate duration
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.info(
                    f"Ingestion completed from {connector.source_name}",
                    extra={
                        'tenant_id': str(self.tenant_id),
                        'source_name': connector.source_name,
                        'duration_seconds': duration,
                        **self.stats
                    }
                )
                
                return {
                    'success': True,
                    'tenant_id': str(self.tenant_id),
                    'source_name': connector.source_name,
                    'duration_seconds': duration,
                    'statistics': self.stats
                }
                
            except Exception as e:
                logger.error(
                    f"Ingestion failed from {connector.source_name}: {str(e)}",
                    extra={
                        'tenant_id': str(self.tenant_id),
                        'source_name': connector.source_name,
                        'error': str(e),
                        **self.stats
                    }
                )
                await db.rollback()
                raise
    
    def _create_db_record(
        self,
        raw_record: RawRecord,
        source_name: str
    ) -> RawIngestionRecord:
        """
        Convert RawRecord to database model.
        
        Args:
            raw_record: Raw record from connector
            source_name: Name of the source
            
        Returns:
            RawIngestionRecord instance
        """
        return RawIngestionRecord(
            id=uuid4(),
            tenant_id=self.tenant_id,
            source=source_name,
            source_id=raw_record.source_id,
            payload=raw_record.payload,
            status='raw',
            ingestion_metadata=raw_record.metadata,
            retrieved_at=raw_record.retrieved_at,
            created_at=datetime.utcnow(),
            retry_count='0'
        )
    
    async def _save_batch(self, db: AsyncSession, batch: List[RawIngestionRecord]) -> None:
        """
        Save a batch of records to database.
        
        Handles duplicate key errors (idempotency).
        
        Args:
            db: Database session
            batch: List of records to save
        """
        for record in batch:
            try:
                db.add(record)
                await db.commit()
                self.stats['records_saved'] += 1
                
                logger.debug(
                    f"Saved record: {record.source_id}",
                    extra={
                        'source_id': record.source_id,
                        'source': record.source
                    }
                )
                
            except IntegrityError as e:
                await db.rollback()
                
                # Check if it's a duplicate key error
                if 'UNIQUE constraint failed' in str(e) or 'uq_raw_ingestion_tenant_source_id' in str(e):
                    self.stats['records_skipped_duplicate'] += 1
                    logger.debug(
                        f"Skipped duplicate record: {record.source_id}",
                        extra={
                            'source_id': record.source_id,
                            'source': record.source
                        }
                    )
                else:
                    self.stats['records_failed'] += 1
                    logger.error(
                        f"Failed to save record: {record.source_id}",
                        extra={
                            'source_id': record.source_id,
                            'error': str(e)
                        }
                    )
            
            except Exception as e:
                await db.rollback()
                self.stats['records_failed'] += 1
                logger.error(
                    f"Failed to save record: {record.source_id}",
                    extra={
                        'source_id': record.source_id,
                        'error': str(e)
                    }
                )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        return self.stats.copy()
