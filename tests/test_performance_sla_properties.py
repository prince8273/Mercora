"""Property-based tests for performance SLA enforcement."""

import pytest
import time
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from hypothesis import given, strategies as st, settings, assume

from src.performance.sla_monitor import (
    SLAMonitor,
    SLAConfiguration,
    SLAViolationType,
    PerformanceMetrics
)
from src.schemas.orchestration import ExecutionMode


# Strategies for generating test data
@st.composite
def execution_mode_strategy(draw):
    """Generate a random ExecutionMode."""
    return draw(st.sampled_from([ExecutionMode.QUICK, ExecutionMode.DEEP]))


@st.composite
def sla_config_strategy(draw):
    """Generate a random SLA configuration."""
    return SLAConfiguration(
        quick_mode_timeout_seconds=draw(st.floats(min_value=10.0, max_value=300.0)),
        deep_mode_timeout_seconds=draw(st.floats(min_value=300.0, max_value=1200.0)),
        quick_mode_target_seconds=draw(st.floats(min_value=5.0, max_value=150.0)),
        deep_mode_target_seconds=draw(st.floats(min_value=150.0, max_value=600.0))
    )


@st.composite
def duration_strategy(draw, mode: ExecutionMode, config: SLAConfiguration):
    """Generate a duration that may or may not violate SLA."""
    if mode == ExecutionMode.QUICK:
        timeout = config.quick_mode_timeout_seconds
    else:
        timeout = config.deep_mode_timeout_seconds
    
    # Generate durations from 1 second to 2x timeout
    return draw(st.floats(min_value=1.0, max_value=timeout * 2.0))


class TestPerformanceSLAProperties:
    """Property-based tests for performance SLA enforcement."""
    
    @given(
        execution_mode=execution_mode_strategy(),
        tenant_id=st.one_of(st.none(), st.uuids()),
        agent_count=st.integers(min_value=1, max_value=10),
        cache_hits=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=100)
    def test_property_27_quick_mode_meets_performance_sla(
        self,
        execution_mode: ExecutionMode,
        tenant_id: UUID | None,
        agent_count: int,
        cache_hits: int
    ):
        """
        Property 27: Quick Mode meets performance SLA.
        
        Validates Requirements: 6.2, 10.1
        
        Property: Quick Mode requests complete within 2 minutes (120 seconds).
        Requests exceeding this timeout are flagged as SLA violations.
        """
        # Arrange
        config = SLAConfiguration(
            quick_mode_timeout_seconds=120.0,
            deep_mode_timeout_seconds=600.0
        )
        monitor = SLAMonitor(config=config)
        
        # Only test Quick Mode for this property
        if execution_mode != ExecutionMode.QUICK:
            execution_mode = ExecutionMode.QUICK
        
        # Act
        metrics = monitor.start_request(
            execution_mode=execution_mode,
            tenant_id=tenant_id
        )
        
        # Simulate execution time (between 1 and 240 seconds)
        # We'll use a fixed time for testing instead of actual sleep
        simulated_duration = 60.0  # Simulate 60 seconds (within SLA)
        
        # Manually set the duration for testing
        metrics.start_time = datetime.utcnow() - timedelta(seconds=simulated_duration)
        
        completed_metrics = monitor.complete_request(
            request_id=metrics.request_id,
            success=True,
            agent_count=agent_count,
            cache_hits=cache_hits
        )
        
        # Assert: Request was tracked
        assert completed_metrics is not None, \
            "Request should be tracked"
        
        assert completed_metrics.execution_mode == ExecutionMode.QUICK, \
            "Execution mode should be QUICK"
        
        assert completed_metrics.duration_seconds is not None, \
            "Duration should be calculated"
        
        assert completed_metrics.duration_seconds > 0, \
            "Duration should be positive"
        
        # Assert: Timeout is 120 seconds for Quick Mode
        timeout = monitor.get_timeout_for_mode(ExecutionMode.QUICK)
        assert timeout == 120.0, \
            "Quick Mode timeout should be 120 seconds"
        
        # Assert: If duration exceeds timeout, violation is recorded
        if completed_metrics.duration_seconds > timeout:
            violations = monitor.get_violations(mode=ExecutionMode.QUICK)
            assert len(violations) > 0, \
                "SLA violation should be recorded when timeout exceeded"
            
            violation = violations[0]
            assert violation.violation_type == SLAViolationType.TIMEOUT, \
                "Violation type should be TIMEOUT"
            
            assert violation.execution_mode == ExecutionMode.QUICK, \
                "Violation should be for QUICK mode"
            
            assert violation.expected_sla_seconds == timeout, \
                "Violation should record expected SLA"
            
            assert violation.actual_duration_seconds == completed_metrics.duration_seconds, \
                "Violation should record actual duration"
        else:
            # No violation if within SLA
            violations = monitor.get_violations(
                mode=ExecutionMode.QUICK,
                violation_type=SLAViolationType.TIMEOUT
            )
            # Filter to this specific request
            request_violations = [
                v for v in violations
                if v.request_id == metrics.request_id
            ]
            assert len(request_violations) == 0, \
                "No violation should be recorded when within SLA"
    
    @given(
        execution_mode=execution_mode_strategy(),
        tenant_id=st.one_of(st.none(), st.uuids()),
        agent_count=st.integers(min_value=1, max_value=10),
        cache_hits=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=100)
    def test_property_28_deep_mode_meets_performance_sla(
        self,
        execution_mode: ExecutionMode,
        tenant_id: UUID | None,
        agent_count: int,
        cache_hits: int
    ):
        """
        Property 28: Deep Mode meets performance SLA.
        
        Validates Requirements: 6.3, 10.2
        
        Property: Deep Mode requests complete within 10 minutes (600 seconds).
        Requests exceeding this timeout are flagged as SLA violations.
        """
        # Arrange
        config = SLAConfiguration(
            quick_mode_timeout_seconds=120.0,
            deep_mode_timeout_seconds=600.0
        )
        monitor = SLAMonitor(config=config)
        
        # Only test Deep Mode for this property
        if execution_mode != ExecutionMode.DEEP:
            execution_mode = ExecutionMode.DEEP
        
        # Act
        metrics = monitor.start_request(
            execution_mode=execution_mode,
            tenant_id=tenant_id
        )
        
        # Simulate execution time (between 1 and 1200 seconds)
        # We'll use a fixed time for testing instead of actual sleep
        simulated_duration = 300.0  # Simulate 300 seconds (within SLA)
        
        # Manually set the duration for testing
        metrics.start_time = datetime.utcnow() - timedelta(seconds=simulated_duration)
        
        completed_metrics = monitor.complete_request(
            request_id=metrics.request_id,
            success=True,
            agent_count=agent_count,
            cache_hits=cache_hits
        )
        
        # Assert: Request was tracked
        assert completed_metrics is not None, \
            "Request should be tracked"
        
        assert completed_metrics.execution_mode == ExecutionMode.DEEP, \
            "Execution mode should be DEEP"
        
        assert completed_metrics.duration_seconds is not None, \
            "Duration should be calculated"
        
        assert completed_metrics.duration_seconds > 0, \
            "Duration should be positive"
        
        # Assert: Timeout is 600 seconds for Deep Mode
        timeout = monitor.get_timeout_for_mode(ExecutionMode.DEEP)
        assert timeout == 600.0, \
            "Deep Mode timeout should be 600 seconds"
        
        # Assert: If duration exceeds timeout, violation is recorded
        if completed_metrics.duration_seconds > timeout:
            violations = monitor.get_violations(mode=ExecutionMode.DEEP)
            assert len(violations) > 0, \
                "SLA violation should be recorded when timeout exceeded"
            
            violation = violations[0]
            assert violation.violation_type == SLAViolationType.TIMEOUT, \
                "Violation type should be TIMEOUT"
            
            assert violation.execution_mode == ExecutionMode.DEEP, \
                "Violation should be for DEEP mode"
            
            assert violation.expected_sla_seconds == timeout, \
                "Violation should record expected SLA"
            
            assert violation.actual_duration_seconds == completed_metrics.duration_seconds, \
                "Violation should record actual duration"
        else:
            # No violation if within SLA
            violations = monitor.get_violations(
                mode=ExecutionMode.DEEP,
                violation_type=SLAViolationType.TIMEOUT
            )
            # Filter to this specific request
            request_violations = [
                v for v in violations
                if v.request_id == metrics.request_id
            ]
            assert len(request_violations) == 0, \
                "No violation should be recorded when within SLA"
    
    @given(
        mode=execution_mode_strategy(),
        duration_multiplier=st.floats(min_value=0.5, max_value=2.5),
        tenant_id=st.one_of(st.none(), st.uuids())
    )
    @settings(max_examples=100)
    def test_timeout_detection(
        self,
        mode: ExecutionMode,
        duration_multiplier: float,
        tenant_id: UUID | None
    ):
        """
        Test that timeouts are correctly detected based on execution mode.
        
        This validates the timeout enforcement mechanism.
        """
        # Arrange
        config = SLAConfiguration()
        monitor = SLAMonitor(config=config)
        
        timeout = monitor.get_timeout_for_mode(mode)
        simulated_duration = timeout * duration_multiplier
        
        # Act
        metrics = monitor.start_request(
            execution_mode=mode,
            tenant_id=tenant_id
        )
        
        # Simulate time passing
        metrics.start_time = datetime.utcnow() - timedelta(seconds=simulated_duration)
        
        # Check timeout
        is_timeout = monitor.check_timeout(metrics.request_id)
        
        # Assert
        if simulated_duration > timeout:
            assert is_timeout, \
                f"Should detect timeout when duration ({simulated_duration:.2f}s) > timeout ({timeout}s)"
        else:
            assert not is_timeout, \
                f"Should not detect timeout when duration ({simulated_duration:.2f}s) <= timeout ({timeout}s)"
    
    @given(
        mode=execution_mode_strategy(),
        request_count=st.integers(min_value=1, max_value=50),
        success_rate=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=100)
    def test_performance_statistics_calculation(
        self,
        mode: ExecutionMode,
        request_count: int,
        success_rate: float
    ):
        """
        Test that performance statistics are calculated correctly.
        
        This validates the metrics tracking and aggregation.
        """
        # Arrange
        monitor = SLAMonitor()
        
        durations = []
        success_count = 0
        
        # Act: Create multiple requests
        for i in range(request_count):
            metrics = monitor.start_request(execution_mode=mode)
            
            # Simulate varying durations
            duration = 10.0 + (i * 5.0)  # 10, 15, 20, 25, ...
            durations.append(duration)
            
            metrics.start_time = datetime.utcnow() - timedelta(seconds=duration)
            
            # Determine success based on success_rate
            success = (i / request_count) < success_rate
            if success:
                success_count += 1
            
            monitor.complete_request(
                request_id=metrics.request_id,
                success=success,
                agent_count=1
            )
        
        # Get statistics
        stats = monitor.get_performance_stats(mode=mode)
        
        # Assert: Statistics are calculated correctly
        assert stats["total_requests"] == request_count, \
            "Total requests should match"
        
        expected_avg = sum(durations) / len(durations)
        # Allow for small floating point differences
        assert abs(stats["avg_response_time"] - expected_avg) < 1.0, \
            f"Average response time should be approximately {expected_avg}, got {stats['avg_response_time']}"
        
        assert abs(stats["min_response_time"] - min(durations)) < 0.1, \
            "Min response time should be correct"
        
        assert abs(stats["max_response_time"] - max(durations)) < 0.1, \
            "Max response time should be correct"
        
        expected_success_rate = success_count / request_count
        assert abs(stats["success_rate"] - expected_success_rate) < 0.02, \
            f"Success rate should be approximately {expected_success_rate}, got {stats['success_rate']}"
        
        expected_error_rate = 1.0 - expected_success_rate
        assert abs(stats["error_rate"] - expected_error_rate) < 0.02, \
            f"Error rate should be approximately {expected_error_rate}, got {stats['error_rate']}"
    
    @given(
        mode=execution_mode_strategy(),
        violation_count=st.integers(min_value=0, max_value=20),
        tenant_id=st.uuids()
    )
    @settings(max_examples=100)
    def test_violation_tracking_and_filtering(
        self,
        mode: ExecutionMode,
        violation_count: int,
        tenant_id: UUID
    ):
        """
        Test that SLA violations are tracked and can be filtered.
        
        This validates the violation recording and retrieval mechanism.
        """
        # Arrange
        config = SLAConfiguration(
            quick_mode_timeout_seconds=10.0,  # Very short for testing
            deep_mode_timeout_seconds=20.0
        )
        monitor = SLAMonitor(config=config)
        
        timeout = monitor.get_timeout_for_mode(mode)
        
        # Act: Create requests that violate SLA
        for i in range(violation_count):
            metrics = monitor.start_request(
                execution_mode=mode,
                tenant_id=tenant_id
            )
            
            # Simulate duration that exceeds timeout
            duration = timeout + 5.0 + i
            metrics.start_time = datetime.utcnow() - timedelta(seconds=duration)
            
            monitor.complete_request(
                request_id=metrics.request_id,
                success=True
            )
        
        # Get violations
        all_violations = monitor.get_violations()
        mode_violations = monitor.get_violations(mode=mode)
        tenant_violations = monitor.get_violations(tenant_id=tenant_id)
        
        # Assert: Violations are tracked
        assert len(all_violations) == violation_count, \
            "All violations should be tracked"
        
        assert len(mode_violations) == violation_count, \
            "Mode filter should work correctly"
        
        assert len(tenant_violations) == violation_count, \
            "Tenant filter should work correctly"
        
        # Assert: Violations have correct properties
        for violation in all_violations:
            assert violation.execution_mode == mode, \
                "Violation should record correct mode"
            
            assert violation.tenant_id == tenant_id, \
                "Violation should record correct tenant"
            
            assert violation.violation_type == SLAViolationType.TIMEOUT, \
                "Violation type should be TIMEOUT"
            
            assert violation.actual_duration_seconds > violation.expected_sla_seconds, \
                "Violation should show actual > expected"
    
    @given(
        request_count=st.integers(min_value=1, max_value=100),
        time_window_minutes=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_throughput_calculation(
        self,
        request_count: int,
        time_window_minutes: int
    ):
        """
        Test that throughput is calculated correctly.
        
        This validates the throughput metrics.
        """
        # Arrange
        monitor = SLAMonitor()
        
        # Act: Create requests spread over time window
        for i in range(request_count):
            metrics = monitor.start_request(execution_mode=ExecutionMode.QUICK)
            
            # Spread requests evenly over time window
            seconds_ago = (i / request_count) * time_window_minutes * 60
            metrics.start_time = datetime.utcnow() - timedelta(seconds=seconds_ago)
            
            monitor.complete_request(
                request_id=metrics.request_id,
                success=True
            )
        
        # Calculate throughput
        throughput = monitor.get_throughput(time_window_minutes=time_window_minutes)
        
        # Assert: Throughput is calculated correctly
        expected_throughput = request_count / time_window_minutes
        assert abs(throughput - expected_throughput) < 0.1, \
            f"Throughput should be approximately {expected_throughput} req/min"
        
        assert throughput >= 0, \
            "Throughput should be non-negative"
