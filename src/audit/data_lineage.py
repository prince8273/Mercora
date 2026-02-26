"""
Data Lineage - Track data transformations and provenance

This module provides data lineage tracking to maintain complete
traceability of data transformations for compliance and auditing.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TransformationType(str, Enum):
    """Types of data transformations"""
    NORMALIZATION = "normalization"
    DEDUPLICATION = "deduplication"
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"
    AGGREGATION = "aggregation"
    FILTERING = "filtering"
    CORRECTION = "correction"


@dataclass
class DataLineage:
    """
    Represents lineage metadata for a data transformation.
    
    Tracks the relationship between source and target records,
    including the transformation applied and metadata.
    """
    id: UUID
    source_record_id: UUID
    target_record_id: UUID
    transformation: TransformationType
    timestamp: datetime
    tenant_id: UUID
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "source_record_id": str(self.source_record_id),
            "target_record_id": str(self.target_record_id),
            "transformation": self.transformation.value,
            "timestamp": self.timestamp.isoformat(),
            "tenant_id": str(self.tenant_id),
            "metadata": self.metadata
        }


class DataLineageTracker:
    """
    Tracks data lineage for all transformations.
    
    Maintains a complete audit trail of data transformations,
    enabling traceability from source to final output.
    """
    
    def __init__(self):
        """Initialize data lineage tracker"""
        self._lineage_records: List[DataLineage] = []
        logger.info("DataLineageTracker initialized")
    
    def log_transformation(
        self,
        source_record_id: UUID,
        target_record_id: UUID,
        transformation: TransformationType,
        tenant_id: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Log a data transformation.
        
        Args:
            source_record_id: UUID of the source record
            target_record_id: UUID of the target/output record
            transformation: Type of transformation applied
            tenant_id: Tenant UUID for isolation
            metadata: Optional metadata about the transformation
            
        Returns:
            UUID of the lineage record
        """
        lineage = DataLineage(
            id=uuid4(),
            source_record_id=source_record_id,
            target_record_id=target_record_id,
            transformation=transformation,
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            metadata=metadata or {}
        )
        
        self._lineage_records.append(lineage)
        
        logger.info(
            f"Logged transformation: {transformation.value} "
            f"({source_record_id} -> {target_record_id})"
        )
        
        return lineage.id
    
    def log_multi_source_transformation(
        self,
        source_record_ids: List[UUID],
        target_record_id: UUID,
        transformation: TransformationType,
        tenant_id: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[UUID]:
        """
        Log a transformation with multiple source records.
        
        Useful for aggregations, joins, or deduplication where
        multiple sources contribute to a single output.
        
        Args:
            source_record_ids: List of source record UUIDs
            target_record_id: UUID of the target/output record
            transformation: Type of transformation applied
            tenant_id: Tenant UUID for isolation
            metadata: Optional metadata about the transformation
            
        Returns:
            List of lineage record UUIDs
        """
        lineage_ids = []
        
        for source_id in source_record_ids:
            lineage_id = self.log_transformation(
                source_record_id=source_id,
                target_record_id=target_record_id,
                transformation=transformation,
                tenant_id=tenant_id,
                metadata=metadata
            )
            lineage_ids.append(lineage_id)
        
        logger.info(
            f"Logged multi-source transformation: {transformation.value} "
            f"({len(source_record_ids)} sources -> {target_record_id})"
        )
        
        return lineage_ids
    
    def get_lineage_for_record(
        self,
        record_id: UUID,
        direction: str = "both"
    ) -> List[DataLineage]:
        """
        Get lineage records for a specific record.
        
        Args:
            record_id: UUID of the record
            direction: "upstream" (sources), "downstream" (targets), or "both"
            
        Returns:
            List of DataLineage records
        """
        if direction == "upstream":
            # Get records where this is the target (find sources)
            records = [
                r for r in self._lineage_records
                if r.target_record_id == record_id
            ]
        elif direction == "downstream":
            # Get records where this is the source (find targets)
            records = [
                r for r in self._lineage_records
                if r.source_record_id == record_id
            ]
        else:  # both
            records = [
                r for r in self._lineage_records
                if r.source_record_id == record_id or r.target_record_id == record_id
            ]
        
        records.sort(key=lambda r: r.timestamp)
        return records
    
    def trace_to_source(
        self,
        record_id: UUID,
        max_depth: int = 10
    ) -> List[DataLineage]:
        """
        Trace a record back to its original source(s).
        
        Recursively follows the lineage chain upstream to find
        all source records.
        
        Args:
            record_id: UUID of the record to trace
            max_depth: Maximum recursion depth
            
        Returns:
            List of DataLineage records in the chain (oldest first)
        """
        chain = []
        visited = set()
        
        def _trace_recursive(current_id: UUID, depth: int):
            if depth >= max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            # Get upstream lineage
            upstream = self.get_lineage_for_record(current_id, direction="upstream")
            
            for lineage in upstream:
                chain.append(lineage)
                _trace_recursive(lineage.source_record_id, depth + 1)
        
        _trace_recursive(record_id, 0)
        
        # Sort by timestamp (oldest first)
        chain.sort(key=lambda r: r.timestamp)
        return chain
    
    def get_lineage_by_transformation(
        self,
        transformation: TransformationType,
        tenant_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[DataLineage]:
        """
        Get lineage records by transformation type.
        
        Args:
            transformation: Type of transformation
            tenant_id: Optional tenant filter
            limit: Maximum number of records to return
            
        Returns:
            List of DataLineage records (newest first)
        """
        records = [
            r for r in self._lineage_records
            if r.transformation == transformation
            and (tenant_id is None or r.tenant_id == tenant_id)
        ]
        
        records.sort(key=lambda r: r.timestamp, reverse=True)
        return records[:limit]
    
    def get_lineage_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 100
    ) -> List[DataLineage]:
        """
        Get all lineage records for a tenant.
        
        Args:
            tenant_id: Tenant UUID
            limit: Maximum number of records to return
            
        Returns:
            List of DataLineage records (newest first)
        """
        records = [
            r for r in self._lineage_records
            if r.tenant_id == tenant_id
        ]
        
        records.sort(key=lambda r: r.timestamp, reverse=True)
        return records[:limit]
    
    def get_transformation_statistics(
        self,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, int]:
        """
        Get statistics on transformations.
        
        Args:
            tenant_id: Optional tenant filter
            
        Returns:
            Dictionary of transformation type -> count
        """
        records = self._lineage_records
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]
        
        stats = {}
        for record in records:
            trans_type = record.transformation.value
            stats[trans_type] = stats.get(trans_type, 0) + 1
        
        return stats
    
    def clear_lineage_for_tenant(self, tenant_id: UUID) -> int:
        """
        Clear all lineage records for a tenant.
        
        Used for tenant cleanup or testing.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Number of records cleared
        """
        original_count = len(self._lineage_records)
        self._lineage_records = [
            r for r in self._lineage_records
            if r.tenant_id != tenant_id
        ]
        cleared = original_count - len(self._lineage_records)
        
        logger.info(f"Cleared {cleared} lineage records for tenant {tenant_id}")
        return cleared
