"""Lifecycle management for data archival, deletion, and storage monitoring."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from src.retention.policy import DataCategory, RetentionPolicy


logger = logging.getLogger(__name__)


@dataclass
class ArchivalMetadata:
    """Metadata for archived data."""
    original_table: str
    original_id: UUID
    archive_date: datetime
    retention_period: timedelta
    tenant_id: Optional[UUID]
    data_category: DataCategory
    archive_location: str  # S3 path or similar
    record_count: int
    size_bytes: int


@dataclass
class StorageUsage:
    """Storage usage metrics."""
    category: DataCategory
    tenant_id: Optional[UUID]
    total_records: int
    total_size_bytes: int
    oldest_record_date: datetime
    newest_record_date: datetime


@dataclass
class StorageAlert:
    """Alert for storage threshold exceedance."""
    alert_type: str  # "threshold_exceeded", "cleanup_suggested"
    category: DataCategory
    tenant_id: Optional[UUID]
    current_usage_bytes: int
    threshold_bytes: int
    suggested_actions: List[str]
    created_at: datetime


class LifecycleManager:
    """
    Manages data lifecycle including archival, deletion, and storage monitoring.
    
    This is a simplified implementation that tracks archival metadata
    and provides storage monitoring. In production, this would integrate
    with actual S3 archival and database deletion operations.
    """
    
    def __init__(
        self,
        retention_policy: RetentionPolicy,
        storage_threshold_bytes: int = 100 * 1024 * 1024 * 1024  # 100 GB default
    ):
        """
        Initialize lifecycle manager.
        
        Args:
            retention_policy: Retention policy configuration
            storage_threshold_bytes: Storage threshold for alerts (default 100GB)
        """
        self.retention_policy = retention_policy
        self.storage_threshold_bytes = storage_threshold_bytes
        self.archival_metadata: List[ArchivalMetadata] = []
        self.storage_alerts: List[StorageAlert] = []
    
    def archive_data(
        self,
        table_name: str,
        record_ids: List[UUID],
        category: DataCategory,
        tenant_id: Optional[UUID] = None,
        archive_location: Optional[str] = None
    ) -> ArchivalMetadata:
        """
        Archive data to cold storage with metadata preservation.
        
        Args:
            table_name: Source table name
            record_ids: List of record IDs to archive
            category: Data category
            tenant_id: Optional tenant ID
            archive_location: Optional custom archive location
            
        Returns:
            Archival metadata
        """
        retention_period = self.retention_policy.get_retention_period(
            category, tenant_id
        )
        
        # Generate archive location if not provided
        if archive_location is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            tenant_prefix = f"tenant_{tenant_id}/" if tenant_id else "global/"
            archive_location = (
                f"s3://data-archive/{tenant_prefix}"
                f"{category.value}/{table_name}_{timestamp}.parquet"
            )
        
        # Create archival metadata
        metadata = ArchivalMetadata(
            original_table=table_name,
            original_id=record_ids[0] if record_ids else UUID(int=0),
            archive_date=datetime.utcnow(),
            retention_period=retention_period,
            tenant_id=tenant_id,
            data_category=category,
            archive_location=archive_location,
            record_count=len(record_ids),
            size_bytes=0  # Would be calculated from actual data
        )
        
        # Store metadata
        self.archival_metadata.append(metadata)
        
        logger.info(
            f"Archived {len(record_ids)} records from {table_name} "
            f"to {archive_location}"
        )
        
        return metadata
    
    def delete_expired_data(
        self,
        table_name: str,
        category: DataCategory,
        tenant_id: Optional[UUID] = None
    ) -> int:
        """
        Delete data that has exceeded its retention period.
        
        Args:
            table_name: Table to clean up
            category: Data category
            tenant_id: Optional tenant ID
            
        Returns:
            Number of records deleted
        """
        retention_period = self.retention_policy.get_retention_period(
            category, tenant_id
        )
        
        cutoff_date = datetime.utcnow() - retention_period
        
        # In production, this would execute actual database deletion
        # For now, we simulate the operation
        deleted_count = 0
        
        logger.info(
            f"Deleted {deleted_count} expired records from {table_name} "
            f"(cutoff: {cutoff_date})"
        )
        
        return deleted_count
    
    def check_storage_usage(
        self,
        current_usage: Dict[DataCategory, StorageUsage]
    ) -> List[StorageAlert]:
        """
        Check storage usage and generate alerts if thresholds exceeded.
        
        Args:
            current_usage: Current storage usage by category
            
        Returns:
            List of storage alerts
        """
        alerts = []
        
        # Calculate total usage
        total_usage_bytes = sum(
            usage.total_size_bytes for usage in current_usage.values()
        )
        
        # Check if total usage exceeds threshold
        if total_usage_bytes > self.storage_threshold_bytes:
            suggested_actions = []
            
            # Identify categories with old data
            for category, usage in current_usage.items():
                retention_period = self.retention_policy.get_retention_period(
                    category, usage.tenant_id
                )
                
                age = datetime.utcnow() - usage.oldest_record_date
                if age > retention_period:
                    suggested_actions.append(
                        f"Archive or delete {category.value} data older than "
                        f"{retention_period.days} days"
                    )
            
            if not suggested_actions:
                suggested_actions.append(
                    "Consider increasing storage capacity or "
                    "adjusting retention policies"
                )
            
            alert = StorageAlert(
                alert_type="threshold_exceeded",
                category=DataCategory.RAW_DATA,  # Generic
                tenant_id=None,
                current_usage_bytes=total_usage_bytes,
                threshold_bytes=self.storage_threshold_bytes,
                suggested_actions=suggested_actions,
                created_at=datetime.utcnow()
            )
            
            alerts.append(alert)
            self.storage_alerts.append(alert)
            
            logger.warning(
                f"Storage threshold exceeded: {total_usage_bytes} bytes "
                f"(threshold: {self.storage_threshold_bytes} bytes)"
            )
        
        return alerts
    
    def get_archival_metadata(
        self,
        category: Optional[DataCategory] = None,
        tenant_id: Optional[UUID] = None
    ) -> List[ArchivalMetadata]:
        """
        Retrieve archival metadata with optional filtering.
        
        Args:
            category: Optional category filter
            tenant_id: Optional tenant filter
            
        Returns:
            List of archival metadata records
        """
        results = self.archival_metadata
        
        if category is not None:
            results = [m for m in results if m.data_category == category]
        
        if tenant_id is not None:
            results = [m for m in results if m.tenant_id == tenant_id]
        
        return results
    
    def schedule_archival_task(
        self,
        category: DataCategory,
        frequency: timedelta = timedelta(days=1)
    ) -> None:
        """
        Schedule periodic archival task for a data category.
        
        Args:
            category: Data category to archive
            frequency: How often to run archival (default: daily)
        """
        # In production, this would integrate with Celery Beat or similar
        logger.info(
            f"Scheduled archival task for {category.value} "
            f"with frequency {frequency}"
        )
