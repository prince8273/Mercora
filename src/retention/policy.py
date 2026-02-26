"""Data retention policy configuration and enforcement."""

from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Dict, Optional
from uuid import UUID


class DataCategory(str, Enum):
    """Categories of data with different retention requirements."""
    RAW_DATA = "raw_data"
    PROCESSED_DATA = "processed_data"
    AGGREGATED_REPORTS = "aggregated_reports"
    DOMAIN_MEMORY = "domain_memory"
    AUDIT_LOGS = "audit_logs"
    MODEL_ARTIFACTS = "model_artifacts"


@dataclass
class RetentionPolicy:
    """
    Defines retention periods for different data categories.
    
    Default retention periods:
    - Raw data: 90 days
    - Processed data: 1 year
    - Aggregated reports: 3 years
    - Domain memory: Configurable (default 1 year)
    - Audit logs: 7 years (compliance)
    - Model artifacts: 2 years
    """
    
    # Default retention periods
    default_periods: Dict[DataCategory, timedelta] = field(default_factory=lambda: {
        DataCategory.RAW_DATA: timedelta(days=90),
        DataCategory.PROCESSED_DATA: timedelta(days=365),
        DataCategory.AGGREGATED_REPORTS: timedelta(days=1095),  # 3 years
        DataCategory.DOMAIN_MEMORY: timedelta(days=365),
        DataCategory.AUDIT_LOGS: timedelta(days=2555),  # 7 years
        DataCategory.MODEL_ARTIFACTS: timedelta(days=730),  # 2 years
    })
    
    # Tenant-specific overrides
    tenant_overrides: Dict[UUID, Dict[DataCategory, timedelta]] = field(default_factory=dict)
    
    def get_retention_period(
        self,
        category: DataCategory,
        tenant_id: Optional[UUID] = None
    ) -> timedelta:
        """
        Get retention period for a data category.
        
        Args:
            category: Data category
            tenant_id: Optional tenant ID for tenant-specific overrides
            
        Returns:
            Retention period as timedelta
        """
        # Check for tenant-specific override
        if tenant_id and tenant_id in self.tenant_overrides:
            tenant_policy = self.tenant_overrides[tenant_id]
            if category in tenant_policy:
                return tenant_policy[category]
        
        # Return default period
        return self.default_periods[category]
    
    def set_tenant_override(
        self,
        tenant_id: UUID,
        category: DataCategory,
        retention_period: timedelta
    ) -> None:
        """
        Set tenant-specific retention override.
        
        Args:
            tenant_id: Tenant ID
            category: Data category
            retention_period: Custom retention period
        """
        if tenant_id not in self.tenant_overrides:
            self.tenant_overrides[tenant_id] = {}
        
        self.tenant_overrides[tenant_id][category] = retention_period
    
    def remove_tenant_override(
        self,
        tenant_id: UUID,
        category: Optional[DataCategory] = None
    ) -> None:
        """
        Remove tenant-specific retention override.
        
        Args:
            tenant_id: Tenant ID
            category: Optional specific category to remove, or None to remove all
        """
        if tenant_id not in self.tenant_overrides:
            return
        
        if category is None:
            # Remove all overrides for tenant
            del self.tenant_overrides[tenant_id]
        elif category in self.tenant_overrides[tenant_id]:
            # Remove specific category override
            del self.tenant_overrides[tenant_id][category]
            
            # Clean up empty tenant entry
            if not self.tenant_overrides[tenant_id]:
                del self.tenant_overrides[tenant_id]
