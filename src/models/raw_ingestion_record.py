"""Raw ingestion record model for storing unprocessed data"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from src.database import Base
from src.models.product import GUID


class RawIngestionRecord(Base):
    """
    Stores raw data from external sources before processing.
    
    This table acts as a staging area for all ingested data, providing:
    - Idempotency through unique constraints
    - Audit trail with metadata
    - Status tracking for processing pipeline
    - Tenant isolation
    """
    __tablename__ = "raw_ingestion_records"
    
    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)
    
    # Tenant isolation
    tenant_id = Column(GUID(), nullable=False, index=True)
    
    # Source identification
    source = Column(String(100), nullable=False, index=True)  # e.g., 'csv_upload', 'competitor_scraper', 'amazon_api'
    source_id = Column(String(255), nullable=False)  # External ID from source system
    
    # Raw data payload
    payload = Column(JSON, nullable=False)  # Raw data as JSON
    
    # Processing status
    status = Column(
        String(20),
        nullable=False,
        default='raw',
        index=True
    )  # raw, validated, failed, processed
    
    # Metadata
    ingestion_metadata = Column(JSON, nullable=True)  # Additional context (source_url, scraper_version, etc.)
    
    # Timestamps
    retrieved_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(String(10), default='0', nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        # Composite index for tenant + source queries
        Index('idx_raw_ingestion_tenant_source', 'tenant_id', 'source'),
        
        # Index for time-based queries
        Index('idx_raw_ingestion_retrieved_at', 'retrieved_at'),
        
        # Index for status filtering
        Index('idx_raw_ingestion_status', 'status'),
        
        # Unique constraint for idempotency
        UniqueConstraint(
            'tenant_id', 'source', 'source_id',
            name='uq_raw_ingestion_tenant_source_id'
        ),
    )
    
    def __repr__(self):
        return (
            f"<RawIngestionRecord("
            f"id={self.id}, "
            f"tenant_id={self.tenant_id}, "
            f"source={self.source}, "
            f"status={self.status}"
            f")>"
        )
    
    def mark_as_processed(self):
        """Mark record as successfully processed"""
        self.status = 'processed'
        self.processed_at = datetime.utcnow()
    
    def mark_as_failed(self, error: str):
        """Mark record as failed with error message"""
        self.status = 'failed'
        self.error_message = error
        self.processed_at = datetime.utcnow()
    
    def mark_as_validated(self):
        """Mark record as validated"""
        self.status = 'validated'
