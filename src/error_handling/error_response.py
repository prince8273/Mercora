"""
Error Response - Standardized Error Handling

This module provides standardized error response formats and error code taxonomy
for consistent error handling across the system.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


class ErrorCode(str, Enum):
    """Error code taxonomy for standardized error handling"""
    
    # Data Quality Errors (1xxx)
    MISSING_DATA = "1001"
    INSUFFICIENT_DATA = "1002"
    DATA_QUALITY_WARNING = "1003"
    INVALID_DATA_FORMAT = "1004"
    STALE_DATA = "1005"
    
    # External Service Errors (2xxx)
    API_FAILURE = "2001"
    API_TIMEOUT = "2002"
    API_RATE_LIMIT = "2003"
    AUTHENTICATION_FAILED = "2004"
    SERVICE_UNAVAILABLE = "2005"
    
    # Processing Errors (3xxx)
    AGENT_EXECUTION_FAILED = "3001"
    MODEL_INFERENCE_FAILED = "3002"
    CONFIDENCE_CALCULATION_FAILED = "3003"
    TIMEOUT_EXCEEDED = "3004"
    RESOURCE_LIMIT_EXCEEDED = "3005"
    
    # Query Errors (4xxx)
    INVALID_QUERY = "4001"
    UNSUPPORTED_QUERY_TYPE = "4002"
    QUERY_PARSING_FAILED = "4003"
    
    # System Errors (5xxx)
    INTERNAL_ERROR = "5001"
    DATABASE_ERROR = "5002"
    CACHE_ERROR = "5003"
    CONFIGURATION_ERROR = "5004"
    
    # Authorization Errors (6xxx)
    UNAUTHORIZED = "6001"
    FORBIDDEN = "6002"
    TENANT_ISOLATION_VIOLATION = "6003"


@dataclass
class ErrorDetail:
    """Detailed error information"""
    field: Optional[str] = None
    message: str = ""
    value: Optional[Any] = None


@dataclass
class ErrorResponse:
    """
    Standardized error response format.
    
    Provides consistent error structure across the system with:
    - Error code taxonomy
    - Human-readable messages
    - Suggested actions for recovery
    - Detailed error context
    """
    
    error_code: ErrorCode
    message: str
    suggested_action: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: List[ErrorDetail] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp.isoformat(),
            "details": [
                {
                    "field": d.field,
                    "message": d.message,
                    "value": d.value
                }
                for d in self.details
            ],
            "context": self.context,
            "recoverable": self.recoverable
        }
    
    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        suggested_action: str = "Contact support if the issue persists"
    ) -> "ErrorResponse":
        """Create error response from exception"""
        return cls(
            error_code=error_code,
            message=str(exception),
            suggested_action=suggested_action,
            context={"exception_type": type(exception).__name__},
            recoverable=False
        )


class ErrorResponseFactory:
    """Factory for creating common error responses with suggested actions"""
    
    @staticmethod
    def missing_data(
        field: str,
        impact: str,
        suggested_action: Optional[str] = None
    ) -> ErrorResponse:
        """Create error response for missing data"""
        return ErrorResponse(
            error_code=ErrorCode.MISSING_DATA,
            message=f"Critical data is missing: {field}",
            suggested_action=suggested_action or f"Provide {field} data to improve analysis accuracy",
            details=[ErrorDetail(field=field, message=impact)],
            recoverable=True
        )
    
    @staticmethod
    def insufficient_data(
        required_data: str,
        current_count: int,
        minimum_count: int
    ) -> ErrorResponse:
        """Create error response for insufficient data"""
        return ErrorResponse(
            error_code=ErrorCode.INSUFFICIENT_DATA,
            message=f"Insufficient data for analysis: {required_data}",
            suggested_action=f"Provide at least {minimum_count} {required_data} records (currently have {current_count})",
            context={
                "required_data": required_data,
                "current_count": current_count,
                "minimum_count": minimum_count
            },
            recoverable=False
        )
    
    @staticmethod
    def data_quality_warning(
        issue: str,
        affected_records: int,
        total_records: int
    ) -> ErrorResponse:
        """Create error response for data quality warnings"""
        percentage = (affected_records / total_records * 100) if total_records > 0 else 0
        return ErrorResponse(
            error_code=ErrorCode.DATA_QUALITY_WARNING,
            message=f"Data quality issue detected: {issue}",
            suggested_action=f"Review and correct {affected_records} affected records ({percentage:.1f}% of data)",
            context={
                "issue": issue,
                "affected_records": affected_records,
                "total_records": total_records,
                "percentage": percentage
            },
            recoverable=True
        )
    
    @staticmethod
    def api_failure(
        service: str,
        retry_count: int,
        fallback_available: bool
    ) -> ErrorResponse:
        """Create error response for API failures"""
        suggested_action = (
            f"Using cached data as fallback" if fallback_available
            else f"Retry the request or check {service} service status"
        )
        return ErrorResponse(
            error_code=ErrorCode.API_FAILURE,
            message=f"External API call failed: {service}",
            suggested_action=suggested_action,
            context={
                "service": service,
                "retry_count": retry_count,
                "fallback_available": fallback_available
            },
            recoverable=fallback_available
        )
    
    @staticmethod
    def agent_execution_failed(
        agent_type: str,
        error_message: str,
        partial_results_available: bool
    ) -> ErrorResponse:
        """Create error response for agent execution failures"""
        suggested_action = (
            "Partial results are available from other agents" if partial_results_available
            else f"Retry the query or check {agent_type} agent configuration"
        )
        return ErrorResponse(
            error_code=ErrorCode.AGENT_EXECUTION_FAILED,
            message=f"Agent execution failed: {agent_type}",
            suggested_action=suggested_action,
            details=[ErrorDetail(field="agent_type", message=error_message, value=agent_type)],
            context={
                "agent_type": agent_type,
                "partial_results_available": partial_results_available
            },
            recoverable=partial_results_available
        )
    
    @staticmethod
    def confidence_unknown(
        reason: str
    ) -> ErrorResponse:
        """Create error response for unknown confidence"""
        return ErrorResponse(
            error_code=ErrorCode.CONFIDENCE_CALCULATION_FAILED,
            message="Confidence score could not be calculated",
            suggested_action="Review data quality and ensure sufficient historical data is available",
            details=[ErrorDetail(message=reason)],
            context={"reason": reason},
            recoverable=True
        )
    
    @staticmethod
    def timeout_exceeded(
        operation: str,
        timeout_seconds: int,
        mode: str
    ) -> ErrorResponse:
        """Create error response for timeout"""
        fallback_mode = "Quick Mode" if mode == "Deep" else None
        suggested_action = (
            f"Try {fallback_mode} for faster results" if fallback_mode
            else "Simplify the query or increase timeout limit"
        )
        return ErrorResponse(
            error_code=ErrorCode.TIMEOUT_EXCEEDED,
            message=f"Operation timed out: {operation}",
            suggested_action=suggested_action,
            context={
                "operation": operation,
                "timeout_seconds": timeout_seconds,
                "mode": mode
            },
            recoverable=bool(fallback_mode)
        )
