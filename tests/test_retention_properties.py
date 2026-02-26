"""Property-based tests for data retention and lifecycle management."""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from hypothesis import given, strategies as st, settings

from src.retention.policy import DataCategory, RetentionPolicy
from src.retention.lifecycle_manager import (
    LifecycleManager,
    ArchivalMetadata,
    StorageUsage,
    StorageAlert
)


# Strategies for generating test data
@st.composite
def data_category_strategy(draw):
    """Generate a random DataCategory."""
    return draw(st.sampled_from(list(DataCategory)))


@st.composite
def retention_period_strategy(draw):
    """Generate a reasonable retention period (1-3650 days)."""
    days = draw(st.integers(min_value=1, max_value=3650))
    return timedelta(days=days)


@st.composite
def storage_usage_strategy(draw):
    """Generate StorageUsage data."""
    category = draw(data_category_strategy())
    tenant_id = draw(st.one_of(st.none(), st.uuids()))
    total_records = draw(st.integers(min_value=0, max_value=1000000))
    total_size_bytes = draw(st.integers(min_value=0, max_value=1000000000000))  # Up to 1TB
    
    # Generate dates with oldest before newest
    days_ago = draw(st.integers(min_value=1, max_value=365))
    oldest_date = datetime.utcnow() - timedelta(days=days_ago)
    newest_date = datetime.utcnow() - timedelta(days=draw(st.integers(min_value=0, max_value=days_ago)))
    
    return StorageUsage(
        category=category,
        tenant_id=tenant_id,
        total_records=total_records,
        total_size_bytes=total_size_bytes,
        oldest_record_date=oldest_date,
        newest_record_date=newest_date
    )


class TestRetentionProperties:
    """Property-based tests for retention and lifecycle management."""
    
    @given(
        category=data_category_strategy(),
        tenant_id=st.one_of(st.none(), st.uuids()),
        custom_period=st.one_of(st.none(), retention_period_strategy())
    )
    @settings(max_examples=100)
    def test_property_43_memory_retention_follows_policy(
        self,
        category: DataCategory,
        tenant_id: UUID | None,
        custom_period: timedelta | None
    ):
        """
        Property 43: Memory retention follows policy.
        
        Validates Requirements: 8.6, 17.2
        
        Property: Data is retained according to configured retention policies,
        with tenant-specific overrides taking precedence over defaults.
        """
        # Arrange
        policy = RetentionPolicy()
        
        # Set custom period if provided
        if custom_period and tenant_id:
            policy.set_tenant_override(tenant_id, category, custom_period)
        
        manager = LifecycleManager(retention_policy=policy)
        
        # Act
        retention_period = policy.get_retention_period(category, tenant_id)
        
        # Assert: Retention period is positive
        assert retention_period.total_seconds() > 0, \
            "Retention period must be positive"
        
        # Assert: If custom period was set, it should be returned
        if custom_period and tenant_id:
            assert retention_period == custom_period, \
                "Tenant-specific override should take precedence"
        else:
            # Should return default period
            assert retention_period == policy.default_periods[category], \
                "Should return default period when no override exists"
        
        # Assert: Cutoff date calculation is correct
        cutoff_date = datetime.utcnow() - retention_period
        assert cutoff_date < datetime.utcnow(), \
            "Cutoff date must be in the past"
        
        # Assert: Data older than cutoff should be eligible for deletion
        old_date = cutoff_date - timedelta(days=1)
        recent_date = cutoff_date + timedelta(days=1)
        
        assert old_date < cutoff_date, \
            "Old data should be before cutoff"
        assert recent_date > cutoff_date, \
            "Recent data should be after cutoff"
    
    @given(
        table_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'P'))),
        record_count=st.integers(min_value=1, max_value=1000),
        category=data_category_strategy(),
        tenant_id=st.one_of(st.none(), st.uuids())
    )
    @settings(max_examples=100)
    def test_property_70_archived_data_retains_metadata(
        self,
        table_name: str,
        record_count: int,
        category: DataCategory,
        tenant_id: UUID | None
    ):
        """
        Property 70: Archived data retains metadata.
        
        Validates Requirements: 17.4
        
        Property: When data is archived, all metadata is preserved including
        source table, record IDs, archive date, retention period, tenant ID,
        category, location, and size information.
        """
        # Arrange
        policy = RetentionPolicy()
        manager = LifecycleManager(retention_policy=policy)
        
        # Generate record IDs
        record_ids = [uuid4() for _ in range(record_count)]
        
        # Act
        metadata = manager.archive_data(
            table_name=table_name,
            record_ids=record_ids,
            category=category,
            tenant_id=tenant_id
        )
        
        # Assert: Metadata is complete
        assert isinstance(metadata, ArchivalMetadata), \
            "Should return ArchivalMetadata object"
        
        assert metadata.original_table == table_name, \
            "Original table name must be preserved"
        
        assert metadata.original_id in record_ids, \
            "Original ID must be from the archived records"
        
        assert metadata.archive_date is not None, \
            "Archive date must be set"
        
        assert metadata.archive_date <= datetime.utcnow(), \
            "Archive date must not be in the future"
        
        assert metadata.retention_period == policy.get_retention_period(category, tenant_id), \
            "Retention period must match policy"
        
        assert metadata.tenant_id == tenant_id, \
            "Tenant ID must be preserved"
        
        assert metadata.data_category == category, \
            "Data category must be preserved"
        
        assert metadata.archive_location is not None, \
            "Archive location must be set"
        
        assert len(metadata.archive_location) > 0, \
            "Archive location must not be empty"
        
        assert metadata.record_count == record_count, \
            "Record count must match input"
        
        assert metadata.size_bytes >= 0, \
            "Size must be non-negative"
        
        # Assert: Metadata is retrievable
        retrieved = manager.get_archival_metadata(category=category, tenant_id=tenant_id)
        assert metadata in retrieved, \
            "Archived metadata must be retrievable"
        
        # Assert: Archive location follows expected pattern
        if tenant_id:
            assert f"tenant_{tenant_id}" in metadata.archive_location, \
                "Tenant-specific archives should include tenant ID in path"
        
        assert category.value in metadata.archive_location, \
            "Archive location should include category"
        
        assert table_name in metadata.archive_location, \
            "Archive location should include table name"
    
    @given(
        usage_data=st.lists(
            storage_usage_strategy(),
            min_size=1,
            max_size=len(DataCategory),
            unique_by=lambda u: u.category
        ),
        threshold_gb=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=100)
    def test_property_71_storage_threshold_exceedance_triggers_alerts(
        self,
        usage_data: list[StorageUsage],
        threshold_gb: int
    ):
        """
        Property 71: Storage threshold exceedance triggers alerts.
        
        Validates Requirements: 17.5
        
        Property: When total storage usage exceeds the configured threshold,
        alerts are generated with current usage, threshold, and suggested actions.
        """
        # Arrange
        threshold_bytes = threshold_gb * 1024 * 1024 * 1024  # Convert GB to bytes
        policy = RetentionPolicy()
        manager = LifecycleManager(
            retention_policy=policy,
            storage_threshold_bytes=threshold_bytes
        )
        
        # Create usage dictionary (now guaranteed unique by category)
        usage_dict = {usage.category: usage for usage in usage_data}
        
        # Calculate total usage from the deduplicated dictionary
        total_usage = sum(usage.total_size_bytes for usage in usage_dict.values())
        
        # Act
        alerts = manager.check_storage_usage(usage_dict)
        
        # Assert: Alerts are generated when threshold exceeded
        if total_usage > threshold_bytes:
            assert len(alerts) > 0, \
                "Alerts must be generated when threshold is exceeded"
            
            alert = alerts[0]
            
            # Assert: Alert contains required information
            assert isinstance(alert, StorageAlert), \
                "Alert must be StorageAlert instance"
            
            assert alert.alert_type in ["threshold_exceeded", "cleanup_suggested"], \
                "Alert type must be valid"
            
            assert alert.current_usage_bytes == total_usage, \
                "Alert must include current usage"
            
            assert alert.threshold_bytes == threshold_bytes, \
                "Alert must include threshold"
            
            assert alert.current_usage_bytes > alert.threshold_bytes, \
                "Alert should only trigger when usage exceeds threshold"
            
            assert len(alert.suggested_actions) > 0, \
                "Alert must include suggested actions"
            
            assert alert.created_at is not None, \
                "Alert must have creation timestamp"
            
            assert alert.created_at <= datetime.utcnow(), \
                "Alert timestamp must not be in the future"
            
            # Assert: Suggested actions are actionable
            for action in alert.suggested_actions:
                assert isinstance(action, str), \
                    "Suggested actions must be strings"
                assert len(action) > 0, \
                    "Suggested actions must not be empty"
            
            # Assert: Alert is stored
            assert alert in manager.storage_alerts, \
                "Alert must be stored in manager"
        else:
            # No alerts should be generated when under threshold
            assert len(alerts) == 0, \
                "No alerts should be generated when under threshold"
    
    @given(
        category=data_category_strategy(),
        tenant_id=st.uuids(),
        override_days=st.integers(min_value=1, max_value=3650)
    )
    @settings(max_examples=100)
    def test_tenant_override_precedence(
        self,
        category: DataCategory,
        tenant_id: UUID,
        override_days: int
    ):
        """
        Test that tenant-specific overrides take precedence over defaults.
        
        This validates the policy enforcement mechanism.
        """
        # Arrange
        policy = RetentionPolicy()
        default_period = policy.get_retention_period(category, None)
        override_period = timedelta(days=override_days)
        
        # Ensure override is different from default
        if override_period == default_period:
            override_period = default_period + timedelta(days=1)
        
        # Act
        policy.set_tenant_override(tenant_id, category, override_period)
        result_period = policy.get_retention_period(category, tenant_id)
        
        # Assert
        assert result_period == override_period, \
            "Tenant override must take precedence"
        assert result_period != default_period, \
            "Override should differ from default"
        
        # Assert: Other tenants still get default
        other_tenant = uuid4()
        other_period = policy.get_retention_period(category, other_tenant)
        assert other_period == default_period, \
            "Other tenants should get default period"
    
    @given(
        categories=st.lists(data_category_strategy(), min_size=1, max_size=len(DataCategory), unique=True),
        record_counts=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=len(DataCategory))
    )
    @settings(max_examples=100)
    def test_archival_metadata_filtering(
        self,
        categories: list[DataCategory],
        record_counts: list[int]
    ):
        """
        Test that archival metadata can be filtered by category and tenant.
        
        This validates the metadata retrieval mechanism.
        """
        # Arrange
        policy = RetentionPolicy()
        manager = LifecycleManager(retention_policy=policy)
        
        tenant1 = uuid4()
        tenant2 = uuid4()
        
        # Archive data for different categories and tenants
        for i, category in enumerate(categories):
            record_count = record_counts[i % len(record_counts)]
            record_ids = [uuid4() for _ in range(record_count)]
            
            # Archive for tenant1
            manager.archive_data(
                table_name=f"table_{category.value}",
                record_ids=record_ids,
                category=category,
                tenant_id=tenant1
            )
            
            # Archive for tenant2
            manager.archive_data(
                table_name=f"table_{category.value}",
                record_ids=record_ids,
                category=category,
                tenant_id=tenant2
            )
        
        # Act & Assert: Filter by category
        for category in categories:
            filtered = manager.get_archival_metadata(category=category)
            assert all(m.data_category == category for m in filtered), \
                "Category filter must work correctly"
            assert len(filtered) >= 2, \
                "Should have archives for both tenants"
        
        # Act & Assert: Filter by tenant
        tenant1_archives = manager.get_archival_metadata(tenant_id=tenant1)
        assert all(m.tenant_id == tenant1 for m in tenant1_archives), \
            "Tenant filter must work correctly"
        assert len(tenant1_archives) == len(categories), \
            "Should have one archive per category for tenant1"
        
        tenant2_archives = manager.get_archival_metadata(tenant_id=tenant2)
        assert all(m.tenant_id == tenant2 for m in tenant2_archives), \
            "Tenant filter must work correctly"
        
        # Act & Assert: Filter by both
        if categories:
            first_category = categories[0]
            filtered_both = manager.get_archival_metadata(
                category=first_category,
                tenant_id=tenant1
            )
            assert all(
                m.data_category == first_category and m.tenant_id == tenant1
                for m in filtered_both
            ), "Combined filter must work correctly"
