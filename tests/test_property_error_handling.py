"""Property-based tests for error handling and data quality"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta

from src.error_handling.error_response import (
    ErrorResponse,
    ErrorResponseFactory,
    ErrorCode
)
from src.error_handling.graceful_degradation import (
    GracefulDegradationHandler,
    FallbackStrategy,
    DegradationResult
)


class TestMissingDataFlagging:
    """
    Property 47: Missing data is flagged in results
    Validates: Requirements 11.1
    """
    
    @given(
        field_name=st.text(min_size=1, max_size=50),
        impact=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=10, deadline=None)
    def test_missing_data_creates_error_response(self, field_name, impact):
        """Test that missing data always creates an error response with flag"""
        error = ErrorResponseFactory.missing_data(field_name, impact)
        
        # Property: Missing data must be flagged
        assert error.error_code == ErrorCode.MISSING_DATA
        assert field_name in error.message or len(error.details) > 0
        assert error.recoverable is True
        assert error.suggested_action is not None
        
        # Property: Error response must be serializable
        error_dict = error.to_dict()
        assert "error_code" in error_dict
        assert "message" in error_dict
        assert "suggested_action" in error_dict
    
    @given(
        successful_count=st.integers(min_value=1, max_value=5),
        failed_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_partial_results_flag_missing_agents(self, successful_count, failed_count):
        """Test that partial results flag missing agent data"""
        handler = GracefulDegradationHandler()
        
        successful_agents = [f"agent_{i}" for i in range(successful_count)]
        failed_agents = [f"failed_agent_{i}" for i in range(failed_count)]
        results = {agent: {"data": f"result_{agent}"} for agent in successful_agents}
        errors = {agent: Exception(f"Error in {agent}") for agent in failed_agents}
        
        result = handler.handle_partial_results(
            successful_agents, failed_agents, results, errors
        )
        
        # Property: Missing data must be flagged in warnings
        assert len(result.warnings) > 0
        assert result.degraded is True
        assert result.fallback_used == FallbackStrategy.PARTIAL_RESULTS
        
        # Property: Each failed agent must have a warning
        assert len(result.warnings) >= failed_count


class TestDataQualityWarnings:
    """
    Property 48: Data quality warnings are included
    Validates: Requirements 11.2
    """
    
    @given(
        issue=st.text(min_size=1, max_size=100),
        affected_records=st.integers(min_value=1, max_value=1000),
        total_records=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=10, deadline=None)
    def test_data_quality_warnings_included(self, issue, affected_records, total_records):
        """Test that data quality issues generate warnings"""
        # Ensure affected <= total
        if affected_records > total_records:
            affected_records, total_records = total_records, affected_records
        
        warning = ErrorResponseFactory.data_quality_warning(
            issue, affected_records, total_records
        )
        
        # Property: Data quality warnings must be included
        assert warning.error_code == ErrorCode.DATA_QUALITY_WARNING
        assert warning.message is not None
        assert warning.suggested_action is not None
        
        # Property: Warning must include context about affected data
        assert "affected_records" in warning.context
        assert "total_records" in warning.context
        assert "percentage" in warning.context
        
        # Property: Percentage must be calculated correctly
        expected_percentage = (affected_records / total_records * 100) if total_records > 0 else 0
        assert abs(warning.context["percentage"] - expected_percentage) < 0.01
    
    @given(
        service=st.text(min_size=1, max_size=50),
        retry_count=st.integers(min_value=0, max_value=5),
        fallback_available=st.booleans()
    )
    @settings(max_examples=10, deadline=None)
    def test_api_failure_includes_quality_warning(self, service, retry_count, fallback_available):
        """Test that API failures include data quality warnings"""
        error = ErrorResponseFactory.api_failure(service, retry_count, fallback_available)
        
        # Property: API failures must include warnings
        assert error.error_code == ErrorCode.API_FAILURE
        assert error.suggested_action is not None
        
        # Property: Recoverable status must match fallback availability
        assert error.recoverable == fallback_available
        
        # Property: Context must include service information
        assert "service" in error.context
        assert "retry_count" in error.context
        assert "fallback_available" in error.context


class TestInsufficientDataExplanation:
    """
    Property 50: Insufficient data produces clear explanations
    Validates: Requirements 11.5
    """
    
    @given(
        required_data=st.text(min_size=1, max_size=50),
        current_count=st.integers(min_value=0, max_value=10),
        minimum_count=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=10, deadline=None)
    def test_insufficient_data_has_clear_explanation(self, required_data, current_count, minimum_count):
        """Test that insufficient data errors provide clear explanations"""
        # Ensure current < minimum for insufficient data scenario
        if current_count >= minimum_count:
            current_count = minimum_count - 1
        
        error = ErrorResponseFactory.insufficient_data(
            required_data, current_count, minimum_count
        )
        
        # Property: Insufficient data must have clear explanation
        assert error.error_code == ErrorCode.INSUFFICIENT_DATA
        assert error.message is not None
        assert required_data in error.message
        
        # Property: Suggested action must explain what data is needed
        assert error.suggested_action is not None
        assert str(minimum_count) in error.suggested_action
        
        # Property: Context must include all relevant counts
        assert error.context["required_data"] == required_data
        assert error.context["current_count"] == current_count
        assert error.context["minimum_count"] == minimum_count
        
        # Property: Must not be recoverable (analysis impossible)
        assert error.recoverable is False
    
    @given(
        reason=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=10, deadline=None)
    def test_confidence_unknown_has_explanation(self, reason):
        """Test that unknown confidence provides clear explanation"""
        error = ErrorResponseFactory.confidence_unknown(reason)
        
        # Property: Unknown confidence must have explanation
        assert error.error_code == ErrorCode.CONFIDENCE_CALCULATION_FAILED
        assert error.message is not None
        assert "confidence" in error.message.lower()
        
        # Property: Must include reason in details or context
        assert len(error.details) > 0 or "reason" in error.context
        
        # Property: Must provide suggested action
        assert error.suggested_action is not None
        assert len(error.suggested_action) > 0
    
    @given(
        operation=st.text(min_size=1, max_size=50),
        timeout_seconds=st.integers(min_value=1, max_value=600),
        mode=st.sampled_from(["Quick", "Deep"])
    )
    @settings(max_examples=10, deadline=None)
    def test_timeout_has_clear_explanation(self, operation, timeout_seconds, mode):
        """Test that timeout errors provide clear explanations"""
        error = ErrorResponseFactory.timeout_exceeded(operation, timeout_seconds, mode)
        
        # Property: Timeout must have clear explanation
        assert error.error_code == ErrorCode.TIMEOUT_EXCEEDED
        assert error.message is not None
        assert operation in error.message
        
        # Property: Must suggest alternative action
        assert error.suggested_action is not None
        
        # Property: Context must include timeout details
        assert error.context["operation"] == operation
        assert error.context["timeout_seconds"] == timeout_seconds
        assert error.context["mode"] == mode
        
        # Property: Deep Mode timeout should suggest Quick Mode fallback
        if mode == "Deep":
            assert "Quick Mode" in error.suggested_action or error.recoverable is True


class TestGracefulDegradation:
    """Additional tests for graceful degradation behavior"""
    
    @given(
        successful_count=st.integers(min_value=0, max_value=5),
        failed_count=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_degradation_result_consistency(self, successful_count, failed_count):
        """Test that degradation results are consistent"""
        handler = GracefulDegradationHandler()
        
        successful_agents = [f"agent_{i}" for i in range(successful_count)]
        failed_agents = [f"failed_agent_{i}" for i in range(failed_count)]
        results = {agent: {"data": f"result_{agent}"} for agent in successful_agents}
        errors = {agent: Exception(f"Error in {agent}") for agent in failed_agents}
        
        result = handler.handle_partial_results(
            successful_agents, failed_agents, results, errors
        )
        
        # Property: Success depends on having at least one successful agent
        assert result.success == (successful_count > 0)
        
        # Property: Degraded flag must be set if any agent failed
        if failed_count > 0:
            assert result.degraded is True
        
        # Property: Result must be serializable
        result_dict = result.to_dict()
        assert "success" in result_dict
        assert "warnings" in result_dict
        assert "degraded" in result_dict
