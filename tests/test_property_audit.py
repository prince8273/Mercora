"""Property-based tests for data lineage and audit trail"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from uuid import uuid4, UUID

from src.audit import (
    DataLineageTracker,
    TransformationType,
    AuditTrailManager,
    OperationType
)


class TestTransformationLogging:
    """
    Property 53: Transformations are logged with lineage
    Validates: Requirements 13.1
    """
    
    @given(
        num_transformations=st.integers(min_value=1, max_value=20),
        transformation_type=st.sampled_from(list(TransformationType))
    )
    @settings(max_examples=10, deadline=None)
    def test_transformations_are_logged(self, num_transformations, transformation_type):
        """Test that all transformations are logged with lineage"""
        tracker = DataLineageTracker()
        tenant_id = uuid4()
        
        # Perform transformations
        lineage_ids = []
        for i in range(num_transformations):
            source_id = uuid4()
            target_id = uuid4()
            
            lineage_id = tracker.log_transformation(
                source_record_id=source_id,
                target_record_id=target_id,
                transformation=transformation_type,
                tenant_id=tenant_id,
                metadata={"index": i}
            )
            lineage_ids.append(lineage_id)
        
        # Property: All transformations must be logged
        assert len(tracker._lineage_records) >= num_transformations
        
        # Property: Each transformation must have a unique ID
        assert len(set(lineage_ids)) == num_transformations
        
        # Property: All logged transformations must have correct type
        for record in tracker._lineage_records:
            if record.tenant_id == tenant_id:
                assert record.transformation == transformation_type
    
    @given(
        num_sources=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_multi_source_transformations_logged(self, num_sources):
        """Test that multi-source transformations are logged correctly"""
        tracker = DataLineageTracker()
        tenant_id = uuid4()
        
        # Create multi-source transformation (e.g., aggregation)
        source_ids = [uuid4() for _ in range(num_sources)]
        target_id = uuid4()
        
        lineage_ids = tracker.log_multi_source_transformation(
            source_record_ids=source_ids,
            target_record_id=target_id,
            transformation=TransformationType.AGGREGATION,
            tenant_id=tenant_id,
            metadata={"aggregation_type": "sum"}
        )
        
        # Property: One lineage record per source
        assert len(lineage_ids) == num_sources
        
        # Property: All sources link to same target
        for source_id in source_ids:
            lineage = tracker.get_lineage_for_record(source_id, direction="downstream")
            assert len(lineage) > 0
            assert all(record.target_record_id == target_id for record in lineage)
    
    @given(
        chain_length=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_lineage_chain_traceability(self, chain_length):
        """Test that lineage chains can be traced to source"""
        tracker = DataLineageTracker()
        tenant_id = uuid4()
        
        # Create transformation chain
        record_ids = [uuid4() for _ in range(chain_length + 1)]
        
        for i in range(chain_length):
            tracker.log_transformation(
                source_record_id=record_ids[i],
                target_record_id=record_ids[i + 1],
                transformation=TransformationType.NORMALIZATION,
                tenant_id=tenant_id
            )
        
        # Property: Can trace final record back to original source
        final_record = record_ids[-1]
        chain = tracker.trace_to_source(final_record)
        
        assert len(chain) >= chain_length
        
        # Property: Chain contains all transformations
        source_ids_in_chain = {record.source_record_id for record in chain}
        target_ids_in_chain = {record.target_record_id for record in chain}
        
        # Original source must be in the chain
        assert record_ids[0] in source_ids_in_chain
        
        # Final target must be in the chain
        assert final_record in target_ids_in_chain


class TestAuditLogQueryability:
    """
    Property 55: Audit logs are queryable
    Validates: Requirements 13.4
    """
    
    @given(
        num_operations=st.integers(min_value=5, max_value=20),
        operation_type=st.sampled_from(list(OperationType))
    )
    @settings(max_examples=10, deadline=None)
    def test_audit_logs_are_queryable(self, num_operations, operation_type):
        """Test that audit logs can be queried by various criteria"""
        manager = AuditTrailManager()
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Log operations
        log_ids = []
        for i in range(num_operations):
            log_id = manager.log_operation(
                operation_type=operation_type,
                record_id=uuid4(),
                record_type="product",
                tenant_id=tenant_id,
                user_id=user_id,
                metadata={"index": i}
            )
            log_ids.append(log_id)
        
        # Property: Can query by tenant
        tenant_logs = manager.query_logs(tenant_id=tenant_id)
        assert len(tenant_logs) >= num_operations
        
        # Property: Can query by operation type
        type_logs = manager.query_logs(
            tenant_id=tenant_id,
            operation_type=operation_type
        )
        assert len(type_logs) >= num_operations
        
        # Property: Can query by user
        user_logs = manager.query_logs(
            tenant_id=tenant_id,
            user_id=user_id
        )
        assert len(user_logs) >= num_operations
        
        # Property: All queried logs must match filters
        for log in tenant_logs:
            assert log.tenant_id == tenant_id
        
        for log in type_logs:
            assert log.operation_type == operation_type
    
    @given(
        num_operations=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_time_range_queries(self, num_operations):
        """Test that audit logs can be queried by time range"""
        manager = AuditTrailManager()
        tenant_id = uuid4()
        
        # Log operations at different times
        start_time = datetime.utcnow()
        
        for i in range(num_operations):
            manager.log_operation(
                operation_type=OperationType.UPDATE,
                record_id=uuid4(),
                record_type="product",
                tenant_id=tenant_id
            )
        
        end_time = datetime.utcnow()
        
        # Property: Can query by time range
        logs = manager.query_logs(
            tenant_id=tenant_id,
            start_time=start_time,
            end_time=end_time
        )
        
        assert len(logs) >= num_operations
        
        # Property: All logs must be within time range
        for log in logs:
            assert start_time <= log.timestamp <= end_time
    
    @given(
        num_operations=st.integers(min_value=5, max_value=15)
    )
    @settings(max_examples=10, deadline=None)
    def test_record_history_retrieval(self, num_operations):
        """Test that complete record history can be retrieved"""
        manager = AuditTrailManager()
        tenant_id = uuid4()
        record_id = uuid4()
        
        # Perform multiple operations on same record
        for i in range(num_operations):
            operation_type = OperationType.UPDATE if i > 0 else OperationType.CREATE
            manager.log_operation(
                operation_type=operation_type,
                record_id=record_id,
                record_type="product",
                tenant_id=tenant_id,
                changes={"price": {"old": i * 10, "new": (i + 1) * 10}}
            )
        
        # Property: Can retrieve complete history for record
        history = manager.get_record_history(record_id, tenant_id)
        
        assert len(history) >= num_operations
        
        # Property: History is in chronological order (oldest first)
        timestamps = [log.timestamp for log in history]
        assert timestamps == sorted(timestamps)
        
        # Property: All history entries are for the same record
        for log in history:
            assert log.record_id == record_id


class TestDeletionAuditing:
    """
    Property 56: Deletions are audited
    Validates: Requirements 13.5
    """
    
    @given(
        num_deletions=st.integers(min_value=1, max_value=20),
        record_type=st.sampled_from(["product", "review", "sales_record"])
    )
    @settings(max_examples=10, deadline=None)
    def test_deletions_are_audited(self, num_deletions, record_type):
        """Test that all deletions are audited"""
        manager = AuditTrailManager()
        tenant_id = uuid4()
        
        # Perform deletions
        deleted_ids = []
        for i in range(num_deletions):
            record_id = uuid4()
            deleted_ids.append(record_id)
            
            manager.log_deletion(
                record_id=record_id,
                record_type=record_type,
                tenant_id=tenant_id,
                deleted_data={"id": str(record_id), "name": f"Item {i}"},
                reason="Data cleanup"
            )
        
        # Property: All deletions must be logged
        deletions = manager.get_deletions(tenant_id=tenant_id)
        assert len(deletions) >= num_deletions
        
        # Property: All deletion logs must have DELETE operation type
        for log in deletions:
            assert log.operation_type == OperationType.DELETE
        
        # Property: Deletion logs must contain deleted record IDs
        logged_ids = {log.record_id for log in deletions if log.tenant_id == tenant_id}
        for deleted_id in deleted_ids:
            assert deleted_id in logged_ids
    
    @given(
        num_deletions=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_deletion_metadata_preserved(self, num_deletions):
        """Test that deletion metadata is preserved"""
        manager = AuditTrailManager()
        tenant_id = uuid4()
        
        # Perform deletions with metadata
        for i in range(num_deletions):
            record_id = uuid4()
            deleted_data = {
                "id": str(record_id),
                "name": f"Product {i}",
                "price": 100 + i
            }
            
            manager.log_deletion(
                record_id=record_id,
                record_type="product",
                tenant_id=tenant_id,
                deleted_data=deleted_data,
                reason=f"Reason {i}"
            )
        
        # Property: Deletion logs must preserve deleted data
        deletions = manager.get_deletions(tenant_id=tenant_id)
        
        for log in deletions:
            if log.tenant_id == tenant_id:
                # Must have metadata
                assert "deleted_data" in log.metadata or "reason" in log.metadata
                
                # If deleted_data exists, it must be a dict
                if "deleted_data" in log.metadata:
                    assert isinstance(log.metadata["deleted_data"], dict)
    
    @given(
        num_deletions=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_deletion_timestamp_accuracy(self, num_deletions):
        """Test that deletion timestamps are accurate"""
        manager = AuditTrailManager()
        tenant_id = uuid4()
        
        before_time = datetime.utcnow()
        
        # Perform deletions
        for i in range(num_deletions):
            manager.log_deletion(
                record_id=uuid4(),
                record_type="product",
                tenant_id=tenant_id
            )
        
        after_time = datetime.utcnow()
        
        # Property: All deletion timestamps must be within operation window
        deletions = manager.get_deletions(tenant_id=tenant_id)
        
        for log in deletions:
            if log.tenant_id == tenant_id:
                assert before_time <= log.timestamp <= after_time


class TestDataCorrections:
    """
    Property 54: Data corrections are audited
    Validates: Requirements 13.3
    """
    
    @given(
        num_corrections=st.integers(min_value=1, max_value=15),
        field_name=st.sampled_from(["price", "quantity", "status", "name"])
    )
    @settings(max_examples=10, deadline=None)
    def test_corrections_are_audited(self, num_corrections, field_name):
        """Test that data corrections are audited with old/new values"""
        manager = AuditTrailManager()
        tenant_id = uuid4()
        
        # Perform corrections
        for i in range(num_corrections):
            record_id = uuid4()
            old_value = i * 10
            new_value = (i + 1) * 10
            
            manager.log_correction(
                record_id=record_id,
                record_type="product",
                tenant_id=tenant_id,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                reason="Data quality improvement"
            )
        
        # Property: All corrections must be logged
        corrections = manager.get_corrections(tenant_id=tenant_id)
        assert len(corrections) >= num_corrections
        
        # Property: Corrections must have CORRECTION operation type
        for log in corrections:
            assert log.operation_type == OperationType.CORRECTION
        
        # Property: Corrections must preserve old and new values
        for log in corrections:
            if log.tenant_id == tenant_id and field_name in log.changes:
                assert "old" in log.changes[field_name]
                assert "new" in log.changes[field_name]


class TestTenantIsolation:
    """Test that audit logs respect tenant isolation"""
    
    @given(
        num_tenants=st.integers(min_value=2, max_value=5),
        operations_per_tenant=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_audit_tenant_isolation(self, num_tenants, operations_per_tenant):
        """Test that audit logs are isolated by tenant"""
        manager = AuditTrailManager()
        
        # Create operations for multiple tenants
        tenant_ids = [uuid4() for _ in range(num_tenants)]
        
        for tenant_id in tenant_ids:
            for i in range(operations_per_tenant):
                manager.log_operation(
                    operation_type=OperationType.CREATE,
                    record_id=uuid4(),
                    record_type="product",
                    tenant_id=tenant_id
                )
        
        # Property: Each tenant can only see their own logs
        for tenant_id in tenant_ids:
            logs = manager.query_logs(tenant_id=tenant_id)
            
            # Must have at least operations_per_tenant logs
            assert len(logs) >= operations_per_tenant
            
            # All logs must belong to this tenant
            for log in logs:
                assert log.tenant_id == tenant_id
    
    @given(
        num_tenants=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_lineage_tenant_isolation(self, num_tenants):
        """Test that lineage records are isolated by tenant"""
        tracker = DataLineageTracker()
        
        # Create lineage for multiple tenants
        tenant_ids = [uuid4() for _ in range(num_tenants)]
        
        for tenant_id in tenant_ids:
            for i in range(5):
                tracker.log_transformation(
                    source_record_id=uuid4(),
                    target_record_id=uuid4(),
                    transformation=TransformationType.NORMALIZATION,
                    tenant_id=tenant_id
                )
        
        # Property: Each tenant can only see their own lineage
        for tenant_id in tenant_ids:
            lineage = tracker.get_lineage_by_tenant(tenant_id)
            
            # Must have at least 5 records
            assert len(lineage) >= 5
            
            # All records must belong to this tenant
            for record in lineage:
                assert record.tenant_id == tenant_id


class TestStatistics:
    """Test audit statistics and reporting"""
    
    @given(
        num_operations=st.integers(min_value=10, max_value=30)
    )
    @settings(max_examples=10, deadline=None)
    def test_audit_statistics(self, num_operations):
        """Test that audit statistics are calculated correctly"""
        manager = AuditTrailManager()
        tenant_id = uuid4()
        
        # Create mix of operations
        operation_types = list(OperationType)
        for i in range(num_operations):
            op_type = operation_types[i % len(operation_types)]
            manager.log_operation(
                operation_type=op_type,
                record_id=uuid4(),
                record_type="product",
                tenant_id=tenant_id
            )
        
        # Property: Statistics must reflect actual operations
        stats = manager.get_statistics(tenant_id=tenant_id)
        
        total_in_stats = sum(stats.values())
        assert total_in_stats >= num_operations
        
        # Property: All operation types in stats must be valid
        for op_type in stats.keys():
            assert op_type in [t.value for t in OperationType]
    
    @given(
        num_transformations=st.integers(min_value=10, max_value=30)
    )
    @settings(max_examples=10, deadline=None)
    def test_lineage_statistics(self, num_transformations):
        """Test that lineage statistics are calculated correctly"""
        tracker = DataLineageTracker()
        tenant_id = uuid4()
        
        # Create mix of transformations
        transformation_types = list(TransformationType)
        for i in range(num_transformations):
            trans_type = transformation_types[i % len(transformation_types)]
            tracker.log_transformation(
                source_record_id=uuid4(),
                target_record_id=uuid4(),
                transformation=trans_type,
                tenant_id=tenant_id
            )
        
        # Property: Statistics must reflect actual transformations
        stats = tracker.get_transformation_statistics(tenant_id=tenant_id)
        
        total_in_stats = sum(stats.values())
        assert total_in_stats >= num_transformations
        
        # Property: All transformation types in stats must be valid
        for trans_type in stats.keys():
            assert trans_type in [t.value for t in TransformationType]
