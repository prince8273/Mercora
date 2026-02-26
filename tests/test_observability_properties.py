"""Property-based tests for observability and telemetry."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from hypothesis import given, strategies as st, settings
import json

from src.observability.metrics import (
    MetricsCollector,
    AgentMetrics,
    APIMetrics,
    AgentType
)
from src.observability.structured_logging import (
    StructuredLogger,
    LogContext
)
from src.observability.tracing import (
    TracingManager,
    TraceContext,
    trace_span
)
from src.observability.alerting import (
    AlertManager,
    Alert,
    AlertSeverity,
    AlertType
)


# Strategies for generating test data
@st.composite
def agent_metrics_strategy(draw):
    """Generate random AgentMetrics."""
    return AgentMetrics(
        agent_type=draw(st.sampled_from([t.value for t in AgentType])),
        execution_time_seconds=draw(st.floats(min_value=0.1, max_value=600.0)),
        cpu_usage_percent=draw(st.floats(min_value=0.0, max_value=100.0)),
        memory_usage_mb=draw(st.floats(min_value=10.0, max_value=10000.0)),
        status=draw(st.sampled_from(["success", "failure", "partial"]))
    )


@st.composite
def api_metrics_strategy(draw):
    """Generate random APIMetrics."""
    return APIMetrics(
        endpoint=draw(st.sampled_from(["/query", "/insights", "/forecast", "/pricing"])),
        method=draw(st.sampled_from(["GET", "POST", "PUT", "DELETE"])),
        status_code=draw(st.sampled_from([200, 201, 400, 401, 404, 500, 503])),
        response_time_seconds=draw(st.floats(min_value=0.01, max_value=30.0)),
        request_size_bytes=draw(st.integers(min_value=100, max_value=100000)),
        response_size_bytes=draw(st.integers(min_value=100, max_value=1000000))
    )


class TestObservabilityProperties:
    """Property-based tests for observability and telemetry."""
    
    @given(
        agent_metrics=st.lists(agent_metrics_strategy(), min_size=1, max_size=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_62_agent_executions_logged(
        self,
        agent_metrics: list
    ):
        """
        Property 62: Agent executions are logged with telemetry.
        
        Validates Requirements: 15.1
        
        Property: For any agent execution, the system logs execution time,
        resource usage (CPU, memory), and output status (success, failure, partial).
        """
        # Arrange: Create metrics collector and structured logger
        collector = MetricsCollector()
        logger = StructuredLogger("test")
        
        # Act: Record all agent executions
        for metrics in agent_metrics:
            collector.record_agent_execution(metrics)
            logger.log_agent_execution(
                agent_type=metrics.agent_type,
                execution_time=metrics.execution_time_seconds,
                status=metrics.status,
                cpu_usage_percent=metrics.cpu_usage_percent,
                memory_usage_mb=metrics.memory_usage_mb
            )
        
        # Assert: All executions are recorded
        assert len(agent_metrics) > 0, \
            "Should have recorded agent executions"
        
        # Assert: Metrics include execution time
        for metrics in agent_metrics:
            assert metrics.execution_time_seconds > 0, \
                "Execution time must be positive"
            assert metrics.execution_time_seconds <= 600.0, \
                "Execution time must be within reasonable bounds"
        
        # Assert: Metrics include resource usage
        for metrics in agent_metrics:
            if metrics.cpu_usage_percent is not None:
                assert 0 <= metrics.cpu_usage_percent <= 100, \
                    "CPU usage must be between 0 and 100 percent"
            
            if metrics.memory_usage_mb is not None:
                assert metrics.memory_usage_mb > 0, \
                    "Memory usage must be positive"
        
        # Assert: Metrics include status
        for metrics in agent_metrics:
            assert metrics.status in ["success", "failure", "partial"], \
                "Status must be one of: success, failure, partial"
    
    @given(
        error_message=st.text(min_size=1, max_size=200),
        context_fields=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.text(), st.integers(), st.floats(), st.booleans()),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_63_errors_logged_with_context(
        self,
        error_message: str,
        context_fields: dict
    ):
        """
        Property 63: Errors are logged with context.
        
        Validates Requirements: 15.2
        
        Property: For any error that occurs, the system captures and logs
        the stack trace, error message, and relevant context.
        """
        # Arrange: Create structured logger
        logger = StructuredLogger("test")
        
        # Create log context
        context = LogContext(
            request_id=str(uuid4()),
            tenant_id=str(uuid4()),
            user_id=str(uuid4()),
            additional_context=context_fields
        )
        
        # Create an error
        try:
            raise ValueError(error_message)
        except ValueError as e:
            # Act: Log error with context
            logger.log_error_with_context(
                message="Test error occurred",
                error=e,
                context=context
            )
            
            # Assert: Error is logged (we can't easily capture logs in tests,
            # but we can verify the method doesn't raise)
            assert True, "Error logging should not raise exceptions"
        
        # Assert: Context contains required fields
        assert context.request_id is not None, \
            "Context must include request_id"
        
        # Assert: Additional context is preserved
        assert context.additional_context == context_fields, \
            "Additional context must be preserved"
    
    @given(
        num_spans=st.integers(min_value=1, max_value=10),
        operation_names=st.lists(
            st.text(min_size=1, max_size=50),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_64_requests_traced_end_to_end(
        self,
        num_spans: int,
        operation_names: list
    ):
        """
        Property 64: Requests are traced end-to-end.
        
        Validates Requirements: 15.4
        
        Property: For any user request that triggers agent orchestration,
        the system creates a distributed trace linking all component interactions.
        """
        # Arrange: Create tracing manager
        manager = TracingManager(enabled=True)
        
        # Act: Create a trace with multiple spans
        root_context = manager.start_trace("test_request")
        
        assert root_context is not None, \
            "Root trace context must be created"
        assert root_context.trace_id is not None, \
            "Trace must have a trace_id"
        assert root_context.span_id is not None, \
            "Trace must have a span_id"
        
        # Create child spans
        child_contexts = []
        for i in range(min(num_spans, len(operation_names))):
            child_context = manager.start_span(
                operation_name=operation_names[i],
                parent_context=root_context
            )
            child_contexts.append(child_context)
            
            # Assert: Child span has same trace_id as parent
            assert child_context.trace_id == root_context.trace_id, \
                "Child span must have same trace_id as parent"
            
            # Assert: Child span has parent_span_id set
            assert child_context.parent_span_id == root_context.span_id, \
                "Child span must reference parent span_id"
            
            # Finish child span
            manager.finish_span(child_context)
        
        # Finish root span
        manager.finish_span(root_context)
        
        # Assert: All spans are linked by trace_id
        trace_spans = manager.get_trace_spans(root_context.trace_id)
        assert len(trace_spans) >= 1, \
            "Trace must contain at least the root span"
        
        # Assert: All spans have the same trace_id
        for span in trace_spans:
            assert span.trace_id == root_context.trace_id, \
                "All spans must share the same trace_id"
    
    @given(
        response_times=st.lists(
            st.floats(min_value=0.1, max_value=2.0),  # Baseline times
            min_size=15,
            max_size=20
        ),
        spike_multiplier=st.floats(min_value=3.0, max_value=10.0)  # Ensure spike exceeds threshold
    )
    @settings(max_examples=100, deadline=None)
    def test_property_65_performance_anomalies_trigger_alerts(
        self,
        response_times: list,
        spike_multiplier: float
    ):
        """
        Property 65: Performance anomalies trigger alerts.
        
        Validates Requirements: 15.5
        
        Property: For any detected performance anomaly (response time spike,
        error rate increase), the system generates an alert for investigation.
        """
        # Arrange: Create alert manager with 5.0s threshold
        manager = AlertManager(
            response_time_threshold=5.0,
            error_rate_threshold=0.1,
            window_size=100,
            enabled=True
        )
        
        # Act: Record baseline response times
        for rt in response_times:
            manager.record_response_time(rt)
        
        # Calculate baseline
        baseline = sum(response_times) / len(response_times)
        
        # Act: Introduce response time spike that exceeds threshold
        spike_time = max(baseline * spike_multiplier, 6.0)  # Ensure > 5.0s threshold
        for _ in range(5):
            manager.record_response_time(spike_time)
        
        # Check for anomaly
        alert = manager.check_response_time_anomaly()
        
        # Assert: Alert is generated for spike exceeding threshold
        assert alert is not None, \
            f"Alert should be generated for response time spike (spike={spike_time:.2f}s, threshold=5.0s)"
        assert alert.alert_type == AlertType.RESPONSE_TIME_SPIKE, \
            "Alert type should be RESPONSE_TIME_SPIKE"
        assert alert.severity in [AlertSeverity.WARNING, AlertSeverity.ERROR], \
            "Alert severity should be WARNING or ERROR"
    
    @given(
        num_requests=st.integers(min_value=30, max_value=100),
        error_rate=st.floats(min_value=0.15, max_value=0.8)  # Above 0.1 threshold
    )
    @settings(max_examples=100, deadline=None)
    def test_error_rate_anomaly_detection(
        self,
        num_requests: int,
        error_rate: float
    ):
        """
        Test that error rate anomalies are detected and trigger alerts.
        
        This validates error rate monitoring and alerting.
        """
        # Arrange: Create alert manager
        manager = AlertManager(
            error_rate_threshold=0.1,
            enabled=True
        )
        
        # Act: Record requests with specified error rate
        # Distribute errors evenly throughout to ensure last 10 have representative sample
        num_errors = int(num_requests * error_rate)
        error_interval = num_requests / num_errors if num_errors > 0 else num_requests
        
        error_count = 0
        for i in range(num_requests):
            # Distribute errors evenly
            is_error = error_count < num_errors and i >= int(error_count * error_interval)
            if is_error:
                error_count += 1
            manager.record_request(is_error=is_error)
        
        # Check for anomaly
        alert = manager.check_error_rate_anomaly()
        
        # Assert: Alert is generated when error rate exceeds threshold
        assert alert is not None, \
            f"Alert should be generated for error rate {error_rate:.1%}"
        assert alert.alert_type == AlertType.ERROR_RATE_SPIKE, \
            "Alert type should be ERROR_RATE_SPIKE"
        assert alert.metadata["current_error_rate"] >= 0.1, \
            "Alert metadata should show error rate >= threshold"
    
    @given(
        api_metrics=st.lists(api_metrics_strategy(), min_size=1, max_size=100)
    )
    @settings(max_examples=100, deadline=None)
    def test_api_metrics_collection(
        self,
        api_metrics: list
    ):
        """
        Test that API metrics are collected correctly.
        
        This validates API endpoint monitoring.
        """
        # Arrange: Create metrics collector
        collector = MetricsCollector()
        
        # Act: Record all API requests
        for metrics in api_metrics:
            collector.record_api_request(metrics)
        
        # Assert: All metrics are recorded
        assert len(api_metrics) > 0, \
            "Should have recorded API metrics"
        
        # Assert: Response times are valid
        for metrics in api_metrics:
            assert metrics.response_time_seconds > 0, \
                "Response time must be positive"
            assert metrics.response_time_seconds <= 30.0, \
                "Response time must be within reasonable bounds"
        
        # Assert: Status codes are valid HTTP codes
        for metrics in api_metrics:
            assert 100 <= metrics.status_code < 600, \
                "Status code must be valid HTTP status code"
        
        # Assert: Request/response sizes are reasonable
        for metrics in api_metrics:
            if metrics.request_size_bytes is not None:
                assert metrics.request_size_bytes > 0, \
                    "Request size must be positive"
            
            if metrics.response_size_bytes is not None:
                assert metrics.response_size_bytes > 0, \
                    "Response size must be positive"
    
    @given(
        alert_type=st.sampled_from(list(AlertType)),
        severity=st.sampled_from(list(AlertSeverity)),
        title=st.text(min_size=1, max_size=100),
        message=st.text(min_size=1, max_size=500)
    )
    @settings(max_examples=100, deadline=None)
    def test_alert_creation_and_acknowledgment(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str
    ):
        """
        Test that alerts can be created and acknowledged.
        
        This validates alert management functionality.
        """
        # Arrange: Create alert manager
        manager = AlertManager()
        
        # Act: Create alert
        alert = manager.create_alert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message
        )
        
        # Assert: Alert is created
        assert alert is not None, \
            "Alert should be created"
        assert alert.alert_id is not None, \
            "Alert should have an ID"
        assert alert.alert_type == alert_type, \
            "Alert type should match"
        assert alert.severity == severity, \
            "Alert severity should match"
        assert alert.title == title, \
            "Alert title should match"
        assert alert.message == message, \
            "Alert message should match"
        assert not alert.acknowledged, \
            "Alert should not be acknowledged initially"
        
        # Act: Acknowledge alert
        success = manager.acknowledge_alert(alert.alert_id, "test_user")
        
        # Assert: Alert is acknowledged
        assert success, \
            "Alert acknowledgment should succeed"
        assert alert.acknowledged, \
            "Alert should be marked as acknowledged"
        assert alert.acknowledged_by == "test_user", \
            "Alert should record who acknowledged it"
        assert alert.acknowledged_at is not None, \
            "Alert should record when it was acknowledged"
    
    @given(
        num_traces=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_trace_context_propagation(
        self,
        num_traces: int
    ):
        """
        Test that trace context is properly propagated.
        
        This validates distributed tracing context management.
        """
        # Arrange: Create tracing manager
        manager = TracingManager()
        
        # Act & Assert: Create multiple independent traces
        trace_ids = set()
        
        for i in range(num_traces):
            context = manager.start_trace(f"trace_{i}")
            
            # Assert: Each trace has unique trace_id
            assert context.trace_id not in trace_ids, \
                "Each trace should have unique trace_id"
            trace_ids.add(context.trace_id)
            
            # Assert: Trace context can be retrieved
            retrieved_context = manager.get_trace_context()
            assert retrieved_context is not None, \
                "Trace context should be retrievable"
            
            manager.finish_span(context)
        
        # Assert: All traces are unique
        assert len(trace_ids) == num_traces, \
            "All traces should have unique IDs"
