"""
Property-based tests for failure escalation and alerting.

Tests Properties 72-77 for Requirements 18.1-18.6.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from src.observability.alerting import (
    AlertManager,
    AlertType,
    AlertSeverity
)


class TestFailureEscalationProperties:
    """Property-based tests for failure escalation."""
    
    @given(
        source_id=st.text(min_size=1, max_size=50),
        failure_count=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=50)
    def test_property_72_repeated_failures_trigger_escalation(
        self,
        source_id,
        failure_count
    ):
        """
        Property 72: Repeated failures trigger escalation.
        
        Validates Requirements: 18.1
        
        GIVEN a source that fails repeatedly
        WHEN the failure count reaches threshold (3+)
        THEN an escalation alert is generated
        AND the alert is marked as CRITICAL
        AND the alert metadata includes escalation target
        """
        # Feature: ecommerce-intelligence-agent, Property 72: Repeated failures trigger escalation
        
        alert_manager = AlertManager(enabled=True)
        
        # Simulate repeated failures
        alert = None
        for i in range(failure_count):
            alert = alert_manager.check_repeated_failures(source_id, failure_threshold=3)
        
        # Property: Alert should be generated after 3+ failures
        assert alert is not None, f"Expected alert after {failure_count} failures"
        assert alert.alert_type == AlertType.REPEATED_FAILURE
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.metadata["source_id"] == source_id
        assert alert.metadata["failure_count"] >= 3
        assert "escalate_to" in alert.metadata
        assert alert.metadata["escalate_to"] == "system_administrators"
    
    @given(
        operation=st.text(min_size=1, max_size=50),
        timeout_seconds=st.floats(min_value=1.0, max_value=60.0),
        actual_seconds=st.floats(min_value=61.0, max_value=120.0)
    )
    @settings(max_examples=50)
    def test_property_73_timeouts_trigger_escalation(
        self,
        operation,
        timeout_seconds,
        actual_seconds
    ):
        """
        Property 73: Timeouts trigger escalation.
        
        Validates Requirements: 18.2
        
        GIVEN an operation that exceeds timeout
        WHEN timeout is detected
        THEN an escalation alert is generated
        AND the alert includes timeout details
        AND repeated timeouts escalate to on-call personnel
        """
        # Feature: ecommerce-intelligence-agent, Property 73: Timeouts trigger escalation
        
        alert_manager = AlertManager(enabled=True)
        
        # First timeout
        alert1 = alert_manager.check_timeout_escalation(
            operation,
            timeout_seconds,
            actual_seconds
        )
        
        # Property: Alert should be generated
        assert alert1 is not None
        assert alert1.alert_type == AlertType.TIMEOUT_ESCALATION
        assert alert1.metadata["operation"] == operation
        assert alert1.metadata["timeout_seconds"] == timeout_seconds
        assert alert1.metadata["actual_seconds"] == actual_seconds
        assert alert1.metadata["timeout_count"] >= 1
        
        # Simulate multiple timeouts
        for _ in range(2):
            alert_manager.check_timeout_escalation(operation, timeout_seconds, actual_seconds)
        
        # Third timeout should escalate to on-call
        alert3 = alert_manager.check_timeout_escalation(operation, timeout_seconds, actual_seconds)
        assert alert3.metadata["timeout_count"] >= 3
        assert alert3.metadata["escalate_to"] == "on_call_personnel"
        assert alert3.severity == AlertSeverity.ERROR
    
    @given(
        error_message=st.text(min_size=10, max_size=100),
        failure_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50)
    def test_property_74_connection_failures_trigger_high_priority_alerts(
        self,
        error_message,
        failure_count
    ):
        """
        Property 74: Connection failures trigger high-priority alerts.
        
        Validates Requirements: 18.3
        
        GIVEN database connection failures
        WHEN failures are detected
        THEN high-priority alerts are generated
        AND persistent failures (3+) are marked CRITICAL
        AND alerts include connection pool status
        """
        # Feature: ecommerce-intelligence-agent, Property 74: Connection failures trigger high-priority alerts
        
        alert_manager = AlertManager(enabled=True)
        
        connection_pool_status = {
            "active_connections": 0,
            "idle_connections": 0,
            "max_connections": 10
        }
        
        # Simulate connection failures
        alert = None
        for i in range(failure_count):
            alert = alert_manager.check_database_connection_failure(
                error_message,
                connection_pool_status
            )
        
        # Property: Alert should be generated
        assert alert is not None
        assert alert.alert_type == AlertType.DATABASE_CONNECTION_FAILURE
        assert alert.metadata["error_message"] == error_message
        assert alert.metadata["failure_count"] == failure_count
        assert "connection_pool_status" in alert.metadata
        assert "escalate_to" in alert.metadata
        
        # Persistent failures should be CRITICAL
        if failure_count >= 3:
            assert alert.severity == AlertSeverity.CRITICAL
            assert alert.metadata["is_persistent"] is True
        else:
            assert alert.severity == AlertSeverity.ERROR
    
    @given(
        component=st.sampled_from(["database", "cache", "api", "scheduler"]),
        error_type=st.sampled_from(["timeout", "connection_refused", "authentication_failed"])
    )
    @settings(max_examples=50)
    def test_property_75_health_check_failures_include_diagnostics(
        self,
        component,
        error_type
    ):
        """
        Property 75: Health check failures include diagnostics.
        
        Validates Requirements: 18.4
        
        GIVEN a health check failure
        WHEN the failure is detected
        THEN an alert is generated with diagnostic information
        AND the alert includes recommended actions
        AND diagnostics are component-specific
        """
        # Feature: ecommerce-intelligence-agent, Property 75: Health check failures include diagnostics
        
        alert_manager = AlertManager(enabled=True)
        
        diagnostics = {
            "error_type": error_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": f"{component} health check failed with {error_type}"
        }
        
        alert = alert_manager.check_health_check_failure(component, diagnostics)
        
        # Property: Alert should include diagnostics
        assert alert is not None
        assert alert.alert_type == AlertType.HEALTH_CHECK_FAILURE
        assert alert.metadata["component"] == component
        assert "diagnostics" in alert.metadata
        assert alert.metadata["diagnostics"] == diagnostics
        assert "recommended_actions" in alert.metadata
        assert len(alert.metadata["recommended_actions"]) > 0
        
        # Verify component-specific actions
        actions = alert.metadata["recommended_actions"]
        if "database" in component:
            assert any("database" in action.lower() for action in actions)
        elif "cache" in component or "redis" in component:
            assert any("redis" in action.lower() or "cache" in action.lower() for action in actions)
    
    @given(
        alert_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=30)
    def test_property_76_alerts_delivered_within_sla(
        self,
        alert_count
    ):
        """
        Property 76: Alerts are delivered within SLA.
        
        Validates Requirements: 18.5
        
        GIVEN alerts are generated
        WHEN alerts are created
        THEN they are delivered within 5-minute SLA
        AND delivery time is tracked
        AND SLA violations are logged
        """
        # Feature: ecommerce-intelligence-agent, Property 76: Alerts are delivered within SLA
        
        alert_manager = AlertManager(enabled=True, alert_delivery_sla_minutes=5)
        
        alerts = []
        for i in range(alert_count):
            alert = alert_manager.create_alert(
                alert_type=AlertType.PERFORMANCE_ANOMALY,
                severity=AlertSeverity.WARNING,
                title=f"Test Alert {i}",
                message=f"Test alert message {i}"
            )
            alerts.append(alert)
        
        # Property: All alerts should have delivery timestamp
        for alert in alerts:
            assert alert.delivered_at is not None
            
            # Calculate delivery time
            delivery_time = (alert.delivered_at - alert.timestamp).total_seconds()
            
            # Delivery should be nearly instantaneous in tests
            assert delivery_time < 1.0, f"Delivery took {delivery_time}s"
            
            # SLA is 5 minutes (300 seconds)
            sla_seconds = alert_manager.alert_delivery_sla_minutes * 60
            assert delivery_time <= sla_seconds
    
    @given(
        alert_count=st.integers(min_value=1, max_value=10),
        user=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=30)
    def test_property_77_alert_acknowledgments_tracked(
        self,
        alert_count,
        user
    ):
        """
        Property 77: Alert acknowledgments are tracked.
        
        Validates Requirements: 18.6
        
        GIVEN alerts are generated
        WHEN alerts are acknowledged and resolved
        THEN acknowledgment details are tracked
        AND resolution time is calculated
        AND resolution notes are stored
        """
        # Feature: ecommerce-intelligence-agent, Property 77: Alert acknowledgments are tracked
        
        alert_manager = AlertManager(enabled=True)
        
        # Create alerts
        alerts = []
        for i in range(alert_count):
            alert = alert_manager.create_alert(
                alert_type=AlertType.ERROR_RATE_SPIKE,
                severity=AlertSeverity.WARNING,
                title=f"Test Alert {i}",
                message=f"Test alert message {i}"
            )
            alerts.append(alert)
        
        # Acknowledge and resolve alerts
        for i, alert in enumerate(alerts):
            # Acknowledge
            success = alert_manager.acknowledge_alert(alert.alert_id, user)
            assert success is True
            
            # Verify acknowledgment tracking
            updated_alert = alert_manager.get_alert(alert.alert_id)
            assert updated_alert.acknowledged is True
            assert updated_alert.acknowledged_by == user
            assert updated_alert.acknowledged_at is not None
            
            # Resolve with notes
            resolution_notes = f"Resolved issue {i}"
            success = alert_manager.resolve_alert(alert.alert_id, user, resolution_notes)
            assert success is True
            
            # Verify resolution tracking
            resolved_alert = alert_manager.get_alert(alert.alert_id)
            assert resolved_alert.resolved is True
            assert resolved_alert.resolved_at is not None
            assert resolved_alert.resolution_notes == resolution_notes
            
            # Verify resolution time calculation
            resolution_time = resolved_alert.get_resolution_time()
            assert resolution_time is not None
            assert resolution_time.total_seconds() >= 0
        
        # Verify statistics include resolution metrics
        stats = alert_manager.get_alert_statistics()
        assert stats["resolved_alerts"] == alert_count
        assert "average_resolution_time_seconds" in stats


class TestFailureEscalationEdgeCases:
    """Edge case tests for failure escalation."""
    
    def test_repeated_failures_reset_on_success(self):
        """Test that failure counts reset after success."""
        alert_manager = AlertManager(enabled=True)
        source_id = "test_source"
        
        # Simulate 2 failures
        for _ in range(2):
            alert_manager.check_repeated_failures(source_id, failure_threshold=3)
        
        # Reset on success
        alert_manager.reset_failure_count(source_id)
        
        # Next failure should not trigger alert
        alert = alert_manager.check_repeated_failures(source_id, failure_threshold=3)
        assert alert is None
    
    def test_database_failures_reset_on_success(self):
        """Test that database failure counts reset after success."""
        alert_manager = AlertManager(enabled=True)
        
        # Simulate failures
        for _ in range(2):
            alert_manager.check_database_connection_failure("Connection error")
        
        # Reset on success
        alert_manager.reset_database_failure_count()
        
        assert alert_manager.db_connection_failures == 0
        assert alert_manager.last_db_failure_time is None
    
    def test_alert_manager_disabled(self):
        """Test that disabled alert manager doesn't generate alerts."""
        alert_manager = AlertManager(enabled=False)
        
        # Try to generate various alerts
        alert1 = alert_manager.check_repeated_failures("source", failure_threshold=3)
        alert2 = alert_manager.check_timeout_escalation("op", 10.0, 20.0)
        alert3 = alert_manager.check_database_connection_failure("error")
        alert4 = alert_manager.check_health_check_failure("component", {})
        
        # All should be None
        assert alert1 is None
        assert alert2 is None
        assert alert3 is None
        assert alert4 is None
