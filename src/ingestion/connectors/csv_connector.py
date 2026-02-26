"""CSV file connector for data ingestion"""
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Dict, Any
from uuid import UUID

from src.ingestion.base import BaseConnector, RawRecord

logger = logging.getLogger(__name__)


class CSVConnector(BaseConnector):
    """
    CSV file connector for ingesting data from CSV files.
    
    Features:
    - Supports incremental pulls (tracks last processed row)
    - Idempotent (uses source_id to prevent duplicates)
    - Validates CSV structure
    - Handles missing fields gracefully
    - Structured JSON logging
    
    CSV Format Requirements:
    - Must have header row
    - Must include a unique identifier column (default: 'sku')
    - All other columns are stored in payload
    """
    
    def __init__(
        self,
        tenant_id: UUID,
        file_path: str,
        source_name: str = "csv_upload",
        id_column: str = "sku",
        data_type: str = "product"
    ):
        """
        Initialize CSV connector.
        
        Args:
            tenant_id: Tenant UUID
            file_path: Path to CSV file
            source_name: Name for this data source
            id_column: Column name to use as source_id
            data_type: Type of data (product, review, sales, etc.)
        """
        super().__init__(tenant_id, source_name)
        self.file_path = Path(file_path)
        self.id_column = id_column
        self.data_type = data_type
        
        # Validate file exists
        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        logger.info(
            "Initialized CSV connector",
            extra={
                'tenant_id': str(tenant_id),
                'file_path': str(file_path),
                'source_name': source_name,
                'data_type': data_type
            }
        )
    
    def fetch(self, *, since: Optional[datetime] = None) -> Iterator[RawRecord]:
        """
        Fetch records from CSV file.
        
        Args:
            since: Only fetch records not yet processed (checks database)
            
        Yields:
            RawRecord objects
            
        Raises:
            ValueError: If CSV format is invalid
        """
        logger.info(
            f"Starting CSV fetch from {self.file_path}",
            extra={
                'tenant_id': str(self.tenant_id),
                'source_name': self.source_name,
                'since': since.isoformat() if since else None
            }
        )
        
        # Get already processed source_ids if doing incremental pull
        processed_ids = set()
        if since:
            processed_ids = self._get_processed_ids(since)
            logger.info(
                f"Found {len(processed_ids)} already processed records",
                extra={'processed_count': len(processed_ids)}
            )
        
        records_yielded = 0
        records_skipped = 0
        retrieved_at = datetime.utcnow()
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Validate header
                if not reader.fieldnames:
                    raise ValueError("CSV file has no header row")
                
                if self.id_column not in reader.fieldnames:
                    raise ValueError(
                        f"ID column '{self.id_column}' not found in CSV. "
                        f"Available columns: {', '.join(reader.fieldnames)}"
                    )
                
                logger.info(
                    f"CSV header validated",
                    extra={
                        'columns': list(reader.fieldnames),
                        'id_column': self.id_column
                    }
                )
                
                # Process each row
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        # Extract source_id
                        source_id = row.get(self.id_column, '').strip()
                        if not source_id:
                            logger.warning(
                                f"Row {row_num} missing {self.id_column}, skipping",
                                extra={'row_number': row_num}
                            )
                            records_skipped += 1
                            continue
                        
                        # Skip if already processed
                        if source_id in processed_ids:
                            logger.debug(
                                f"Skipping already processed record: {source_id}",
                                extra={'source_id': source_id}
                            )
                            records_skipped += 1
                            continue
                        
                        # Create payload (all columns)
                        payload = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
                        
                        # Create metadata
                        metadata = {
                            'source_file': str(self.file_path.name),
                            'row_number': row_num,
                            'data_type': self.data_type,
                            'column_count': len(row)
                        }
                        
                        # Yield record
                        record = RawRecord(
                            source_id=source_id,
                            payload=payload,
                            retrieved_at=retrieved_at,
                            metadata=metadata
                        )
                        
                        yield record
                        records_yielded += 1
                        
                    except Exception as e:
                        logger.error(
                            f"Error processing row {row_num}: {str(e)}",
                            extra={
                                'row_number': row_num,
                                'error': str(e)
                            }
                        )
                        records_skipped += 1
                        continue
        
        except Exception as e:
            logger.error(
                f"Error reading CSV file: {str(e)}",
                extra={
                    'file_path': str(self.file_path),
                    'error': str(e)
                }
            )
            raise
        
        logger.info(
            f"CSV fetch completed",
            extra={
                'records_yielded': records_yielded,
                'records_skipped': records_skipped,
                'total_processed': records_yielded + records_skipped
            }
        )
    
    def _get_processed_ids(self, since: datetime) -> set:
        """
        Get source_ids that have already been processed since a given time.
        
        Note: This method is a placeholder for incremental pulls.
        In production, this would query the database asynchronously.
        For now, returns empty set (processes all records).
        
        Args:
            since: Only check records created after this time
            
        Returns:
            Set of source_ids
        """
        # TODO: Implement async database query for processed IDs
        # For now, return empty set to process all records
        logger.info("Incremental pull not yet implemented, processing all records")
        return set()
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the CSV source"""
        info = super().get_source_info()
        info.update({
            'file_path': str(self.file_path),
            'file_exists': self.file_path.exists(),
            'file_size_bytes': self.file_path.stat().st_size if self.file_path.exists() else 0,
            'id_column': self.id_column,
            'data_type': self.data_type
        })
        return info
