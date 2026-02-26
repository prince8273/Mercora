"""
Audit Trail - Track data operations for compliance

This module provides audit logging for all data operations including
corrections, deletions, and updates to maintain compliance.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """Types of data operations"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    CORRECTION = "correction"
    VALIDATION = "validation"


@dataclass
class AuditLog:
    """
    Represents an audit log entry for a data operation.
    
    Tracks who did what, when, and what changed.
    """
    id: UUID
    operation_type: OperationType
    record_id: UUID
    record_type: str  # e.g., "product", "review", "sales_record"
    tenant_id: UUID
    timestamp: datetime
    user_id: Optional[UUID] = None
    changes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "operation_type": self.operation_type.value,
            "record_id": str(self.record_id),
            "record_type": self.record_type,
            "tenant_id": str(self.tenant_id),
            "timestamp": self.timestamp.isoformat(),
            "user_id": str(self.user_id) if self.user_id else None,
            "changes": self.changes,
            "metadata": self.metadata
        }


class AuditTrailManager:
    """
    Manages audit trail for all data operations.
    
    Provides logging and querying capabilities for compliance
    and traceability requirements.
    """
    
    def __init__(self):
        """Initialize audit trail manager"""
        self._audit_logs: List[AuditLog] = []
        logger.info("AuditTrailManager initialized")
    
    def log_operation(
        self,
        operation_type: OperationType,
        record_id: UUID,
        record_type: str,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Log a data operation.
        
        Args:
            operation_type: Type of operation performed
            record_id: UUID of the affected record
            record_type: Type of record (e.g., "product", "review")
            tenant_id: Tenant UUID for isolation
            user_id: Optional user who performed the operation
            changes: Optional dictionary of changes (old_value -> new_value)
            metadata: Optional metadata about the operation
            
        Returns:
            UUID of the audit log entry
        """
        audit_log = AuditLog(
            id=uuid4(),
            operation_type=operation_type,
            record_id=record_id,
            record_type=record_type,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            changes=changes or {},
            metadata=metadata or {}
        )
        
        self._audit_logs.append(audit_log)
        
        logger.info(
            f"Logged {operation_type.value} operation on {record_type} "
            f"record {record_id}"
        )
        
        return audit_log.id
    
    def log_correction(
        self,
        record_id: UUID,
        record_type: str,
        tenant_id: UUID,
        field_name: str,
        old_value: Any,
        new_value: Any,
        reason: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> UUID:
        """
        Log a data quality correction.
        
        Args:
            record_id: UUID of the corrected record
            record_type: Type of record
            tenant_id: Tenant UUID
            field_name: Name of the corrected field
            old_value: Original value before correction
            new_value: New value after correction
            reason: Optional reason for correction
            user_id: Optional user who made the correction
            
        Returns:
            UUID of the audit log entry
        """
        changes = {
            field_name: {
                "old": old_value,
                "new": new_value
            }
        }
        
        metadata = {}
        if reason:
            metadata["reason"] = reason
        
        return self.log_operation(
            operation_type=OperationType.CORRECTION,
            record_id=record_id,
            record_type=record_type,
            tenant_id=tenant_id,
            user_id=user_id,
            changes=changes,
            metadata=metadata
        )
    
    def log_deletion(
        self,
        record_id: UUID,
        record_type: str,
        tenant_id: UUID,
        deleted_data: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> UUID:
        """
        Log a data deletion operation.
        
        Args:
            record_id: UUID of the deleted record
            record_type: Type of record
            tenant_id: Tenant UUID
            deleted_data: Optional snapshot of deleted data
            reason: Optional reason for deletion
            user_id: Optional user who performed deletion
            
        Returns:
            UUID of the audit log entry
        """
        metadata = {}
        if reason:
            metadata["reason"] = reason
        if deleted_data:
            metadata["deleted_data"] = deleted_data
        
        return self.log_operation(
            operation_type=OperationType.DELETE,
            record_id=record_id,
            record_type=record_type,
            tenant_id=tenant_id,
            user_id=user_id,
            metadata=metadata
        )
    
    def query_logs(
        self,
        tenant_id: Optional[UUID] = None,
        operation_type: Optional[OperationType] = None,
        record_id: Optional[UUID] = None,
        record_type: Optional[str] = None,
        user_id: Optional[UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Query audit logs with filters.
        
        Args:
            tenant_id: Optional tenant filter
            operation_type: Optional operation type filter
            record_id: Optional specific record filter
            record_type: Optional record type filter
            user_id: Optional user filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of results
            
        Returns:
            List of matching audit logs (newest first)
        """
        results = self._audit_logs
        
        # Apply filters
        if tenant_id:
            results = [log for log in results if log.tenant_id == tenant_id]
        
        if operation_type:
            results = [log for log in results if log.operation_type == operation_type]
        
        if record_id:
            results = [log for log in results if log.record_id == record_id]
        
        if record_type:
            results = [log for log in results if log.record_type == record_type]
        
        if user_id:
            results = [log for log in results if log.user_id == user_id]
        
        if start_time:
            results = [log for log in results if log.timestamp >= start_time]
        
        if end_time:
            results = [log for log in results if log.timestamp <= end_time]
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda log: log.timestamp, reverse=True)
        
        return results[:limit]
    
    def get_record_history(
        self,
        record_id: UUID,
        tenant_id: Optional[UUID] = None
    ) -> List[AuditLog]:
        """
        Get complete history for a specific record.
        
        Args:
            record_id: UUID of the record
            tenant_id: Optional tenant filter
            
        Returns:
            List of audit logs for the record (oldest first)
        """
        logs = self.query_logs(
            record_id=record_id,
            tenant_id=tenant_id,
            limit=1000
        )
        
        # Return in chronological order (oldest first)
        return list(reversed(logs))
    
    def get_deletions(
        self,
        tenant_id: Optional[UUID] = None,
        record_type: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get all deletion operations.
        
        Args:
            tenant_id: Optional tenant filter
            record_type: Optional record type filter
            limit: Maximum number of results
            
        Returns:
            List of deletion audit logs (newest first)
        """
        return self.query_logs(
            tenant_id=tenant_id,
            operation_type=OperationType.DELETE,
            record_type=record_type,
            limit=limit
        )
    
    def get_corrections(
        self,
        tenant_id: Optional[UUID] = None,
        record_type: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get all correction operations.
        
        Args:
            tenant_id: Optional tenant filter
            record_type: Optional record type filter
            limit: Maximum number of results
            
        Returns:
            List of correction audit logs (newest first)
        """
        return self.query_logs(
            tenant_id=tenant_id,
            operation_type=OperationType.CORRECTION,
            record_type=record_type,
            limit=limit
        )
    
    def get_statistics(
        self,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, int]:
        """
        Get statistics on audit operations.
        
        Args:
            tenant_id: Optional tenant filter
            
        Returns:
            Dictionary of operation type -> count
        """
        logs = self._audit_logs
        if tenant_id:
            logs = [log for log in logs if log.tenant_id == tenant_id]
        
        stats = {}
        for log in logs:
            op_type = log.operation_type.value
            stats[op_type] = stats.get(op_type, 0) + 1
        
        return stats
    
    def clear_logs_for_tenant(self, tenant_id: UUID) -> int:
        """
        Clear all audit logs for a tenant.
        
        Used for tenant cleanup or testing.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Number of logs cleared
        """
        original_count = len(self._audit_logs)
        self._audit_logs = [
            log for log in self._audit_logs
            if log.tenant_id != tenant_id
        ]
        cleared = original_count - len(self._audit_logs)
        
        logger.info(f"Cleared {cleared} audit logs for tenant {tenant_id}")
        return cleared
