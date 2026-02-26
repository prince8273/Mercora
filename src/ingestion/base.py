"""Base connector interface for data ingestion"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterator, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class RawRecord(BaseModel):
    """
    Raw data record from external source.
    
    This is the standardized format that all connectors must return.
    """
    source_id: str = Field(..., description="Unique identifier from source system")
    payload: Dict[str, Any] = Field(..., description="Raw data as dictionary")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow, description="When data was retrieved")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the record")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "PROD001",
                "payload": {
                    "sku": "PROD001",
                    "name": "Wireless Mouse",
                    "price": 29.99,
                    "currency": "USD"
                },
                "retrieved_at": "2026-02-20T10:30:00",
                "metadata": {
                    "source_file": "products.csv",
                    "row_number": 1
                }
            }
        }
    )


class BaseConnector(ABC):
    """
    Abstract base class for all data connectors.
    
    All connectors must implement:
    - fetch(): Retrieve records from source
    - ack(): Acknowledge successful processing (optional)
    
    Connectors are responsible for:
    - Authentication with source systems
    - Pagination and incremental pulls
    - Rate limiting
    - Error handling and retries
    - Converting source data to RawRecord format
    """
    
    def __init__(self, tenant_id: UUID, source_name: str):
        """
        Initialize connector.
        
        Args:
            tenant_id: Tenant UUID for isolation
            source_name: Name of the data source (e.g., 'csv_upload', 'amazon_api')
        """
        self.tenant_id = tenant_id
        self.source_name = source_name
    
    @abstractmethod
    def fetch(self, *, since: Optional[datetime] = None) -> Iterator[RawRecord]:
        """
        Fetch records from source.
        
        This method should yield RawRecord objects one at a time for memory efficiency.
        Supports incremental pulls using the 'since' parameter.
        
        Args:
            since: Only fetch records modified/created after this timestamp (optional)
            
        Yields:
            RawRecord objects
            
        Raises:
            ConnectionError: If unable to connect to source
            ValueError: If data format is invalid
        """
        pass
    
    def ack(self, record_id: str) -> None:
        """
        Acknowledge successful processing of a record.
        
        Optional method for connectors that support acknowledgment.
        Default implementation does nothing.
        
        Args:
            record_id: ID of the successfully processed record
        """
        pass
    
    def get_source_info(self) -> Dict[str, Any]:
        """
        Get information about the data source.
        
        Returns:
            Dictionary with source metadata
        """
        return {
            'tenant_id': str(self.tenant_id),
            'source_name': self.source_name,
            'connector_type': self.__class__.__name__
        }
