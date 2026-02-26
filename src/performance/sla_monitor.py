"""Performance SLA monitoring and enforcement."""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from src.schemas.orchestration import ExecutionMode


logger = logging.getLogger(__name__)


class SLAViolationType(str, Enum):
    """Types of SLA violations."""
    TIMEOUT = "timeout"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"


@dataclass
class PerformanceMetrics:
    """Performance metrics for a request."""
    request_id: UUID
    tenant_id: Optional[UUID]
    execution_mode: ExecutionMode
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    agent_count: int = 0
    cache_hits: int = 0
    
    def complete(self, success: bool = True, error: Optional[str] = None):
        """Mark the request as complete."""
        self.end_time = datetime.utcnow()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.error = error


@dataclass
class SLAViolation:
    """Record of an SLA violation."""
    violation_id: UUID
    request_id: UUID
    tenant_id: Optional[UUID]
    violation_type: SLAViolationType
    execution_mode: ExecutionMode
    expected_sla_seconds: float
    actual_duration_seconds: float
    timestamp: datetime
    details: Dict[str, any] = field(default_factory=dict)


@dataclass
class SLAConfiguration:
    """SLA configuration for different execution modes."""
    quick_mode_timeout_seconds: float = 120.0  # 2 minutes
    deep_mode_timeout_seconds: float = 600.0   # 10 minutes
    quick_mode_target_seconds: float = 90.0    # Target 90s for Quick Mode
    deep_mode_target_seconds: float = 480.0    # Target 8 minutes for Deep Mode
    error_rate_threshold: float = 0.05         # 5% error rate threshold
    throughput_min_requests_per_minute: float = 10.0


class SLAMonitor:
    """
    Monitors and enforces performance SLAs.
    
    Tracks:
    - Request response times
    - Timeout enforcement
    - Throughput metrics
    - Error rates
    - SLA violations
    """
    
    def __init__(self, config: Optional[SLAConfiguration] = None):
        """
        Initialize SLA monitor.
        
        Args:
            config: SLA configuration (uses defaults if not provided)
        """
        self.config = config or SLAConfiguration()
        self.active_requests: Dict[UUID, PerformanceMetrics] = {}
        self.completed_requests: List[PerformanceMetrics] = []
        self.violations: List[SLAViolation] = []
        self._request_window_minutes = 5  # Track last 5 minutes for throughput
    
    def start_request(
        self,
        execution_mode: ExecutionMode,
        tenant_id: Optional[UUID] = None,
        request_id: Optional[UUID] = None
    ) -> PerformanceMetrics:
        """
        Start tracking a new request.
        
        Args:
            execution_mode: Execution mode (Quick or Deep)
            tenant_id: Optional tenant ID
            request_id: Optional request ID (generated if not provided)
            
        Returns:
            Performance metrics object for this request
        """
        if request_id is None:
            request_id = uuid4()
        
        metrics = PerformanceMetrics(
            request_id=request_id,
            tenant_id=tenant_id,
            execution_mode=execution_mode,
            start_time=datetime.utcnow()
        )
        
        self.active_requests[request_id] = metrics
        
        logger.info(
            f"Started tracking request {request_id} "
            f"in {execution_mode.value} mode"
        )
        
        return metrics
    
    def complete_request(
        self,
        request_id: UUID,
        success: bool = True,
        error: Optional[str] = None,
        agent_count: int = 0,
        cache_hits: int = 0
    ) -> Optional[PerformanceMetrics]:
        """
        Complete a request and check for SLA violations.
        
        Args:
            request_id: Request ID
            success: Whether the request succeeded
            error: Optional error message
            agent_count: Number of agents executed
            cache_hits: Number of cache hits
            
        Returns:
            Performance metrics if request was found, None otherwise
        """
        if request_id not in self.active_requests:
            logger.warning(f"Request {request_id} not found in active requests")
            return None
        
        metrics = self.active_requests.pop(request_id)
        metrics.complete(success=success, error=error)
        metrics.agent_count = agent_count
        metrics.cache_hits = cache_hits
        
        self.completed_requests.append(metrics)
        
        # Check for SLA violations
        self._check_sla_violation(metrics)
        
        logger.info(
            f"Completed request {request_id} in {metrics.duration_seconds:.2f}s "
            f"(mode: {metrics.execution_mode.value}, success: {success})"
        )
        
        return metrics
    
    def check_timeout(self, request_id: UUID) -> bool:
        """
        Check if a request has exceeded its timeout.
        
        Args:
            request_id: Request ID to check
            
        Returns:
            True if request has timed out, False otherwise
        """
        if request_id not in self.active_requests:
            return False
        
        metrics = self.active_requests[request_id]
        elapsed = (datetime.utcnow() - metrics.start_time).total_seconds()
        
        timeout = self._get_timeout_for_mode(metrics.execution_mode)
        
        if elapsed > timeout:
            logger.warning(
                f"Request {request_id} timed out after {elapsed:.2f}s "
                f"(timeout: {timeout}s, mode: {metrics.execution_mode.value})"
            )
            return True
        
        return False
    
    def get_timeout_for_mode(self, execution_mode: ExecutionMode) -> float:
        """
        Get timeout in seconds for an execution mode.
        
        Args:
            execution_mode: Execution mode
            
        Returns:
            Timeout in seconds
        """
        return self._get_timeout_for_mode(execution_mode)
    
    def _get_timeout_for_mode(self, execution_mode: ExecutionMode) -> float:
        """Internal method to get timeout."""
        if execution_mode == ExecutionMode.QUICK:
            return self.config.quick_mode_timeout_seconds
        else:  # DEEP
            return self.config.deep_mode_timeout_seconds
    
    def _get_target_for_mode(self, execution_mode: ExecutionMode) -> float:
        """Get target response time for an execution mode."""
        if execution_mode == ExecutionMode.QUICK:
            return self.config.quick_mode_target_seconds
        else:  # DEEP
            return self.config.deep_mode_target_seconds
    
    def _check_sla_violation(self, metrics: PerformanceMetrics) -> None:
        """
        Check if a completed request violated SLA.
        
        Args:
            metrics: Performance metrics to check
        """
        if metrics.duration_seconds is None:
            return
        
        timeout = self._get_timeout_for_mode(metrics.execution_mode)
        
        # Check timeout violation
        if metrics.duration_seconds > timeout:
            violation = SLAViolation(
                violation_id=uuid4(),
                request_id=metrics.request_id,
                tenant_id=metrics.tenant_id,
                violation_type=SLAViolationType.TIMEOUT,
                execution_mode=metrics.execution_mode,
                expected_sla_seconds=timeout,
                actual_duration_seconds=metrics.duration_seconds,
                timestamp=datetime.utcnow(),
                details={
                    "success": metrics.success,
                    "error": metrics.error,
                    "agent_count": metrics.agent_count
                }
            )
            
            self.violations.append(violation)
            
            logger.error(
                f"SLA VIOLATION: Request {metrics.request_id} exceeded timeout "
                f"({metrics.duration_seconds:.2f}s > {timeout}s)"
            )
        
        # Check target response time (warning, not violation)
        target = self._get_target_for_mode(metrics.execution_mode)
        if metrics.duration_seconds > target and metrics.success:
            logger.warning(
                f"Request {metrics.request_id} exceeded target response time "
                f"({metrics.duration_seconds:.2f}s > {target}s)"
            )
    
    def get_performance_stats(
        self,
        mode: Optional[ExecutionMode] = None,
        tenant_id: Optional[UUID] = None,
        time_window_minutes: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Get performance statistics.
        
        Args:
            mode: Optional filter by execution mode
            tenant_id: Optional filter by tenant
            time_window_minutes: Optional time window (default: all time)
            
        Returns:
            Dictionary of performance statistics
        """
        # Filter requests
        requests = self.completed_requests
        
        if time_window_minutes:
            cutoff = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            requests = [r for r in requests if r.start_time >= cutoff]
        
        if mode:
            requests = [r for r in requests if r.execution_mode == mode]
        
        if tenant_id:
            requests = [r for r in requests if r.tenant_id == tenant_id]
        
        if not requests:
            return {
                "total_requests": 0,
                "avg_response_time": 0.0,
                "min_response_time": 0.0,
                "max_response_time": 0.0,
                "success_rate": 0.0,
                "error_rate": 0.0,
                "sla_compliance_rate": 0.0
            }
        
        # Calculate statistics
        durations = [
            r.duration_seconds 
            for r in requests 
            if r.duration_seconds is not None
        ]
        successes = sum(1 for r in requests if r.success)
        
        # Count SLA violations in this set
        request_ids = {r.request_id for r in requests}
        violations_in_set = [
            v for v in self.violations
            if v.request_id in request_ids
        ]
        
        return {
            "total_requests": len(requests),
            "avg_response_time": sum(durations) / len(durations) if durations else 0.0,
            "min_response_time": min(durations) if durations else 0.0,
            "max_response_time": max(durations) if durations else 0.0,
            "success_rate": successes / len(requests) if requests else 0.0,
            "error_rate": (len(requests) - successes) / len(requests) if requests else 0.0,
            "sla_compliance_rate": (len(requests) - len(violations_in_set)) / len(requests) if requests else 0.0,
            "total_violations": len(violations_in_set)
        }
    
    def get_violations(
        self,
        mode: Optional[ExecutionMode] = None,
        tenant_id: Optional[UUID] = None,
        violation_type: Optional[SLAViolationType] = None,
        limit: int = 100
    ) -> List[SLAViolation]:
        """
        Get SLA violations with optional filtering.
        
        Args:
            mode: Optional filter by execution mode
            tenant_id: Optional filter by tenant
            violation_type: Optional filter by violation type
            limit: Maximum number of violations to return
            
        Returns:
            List of SLA violations
        """
        violations = self.violations
        
        if mode:
            violations = [v for v in violations if v.execution_mode == mode]
        
        if tenant_id:
            violations = [v for v in violations if v.tenant_id == tenant_id]
        
        if violation_type:
            violations = [v for v in violations if v.violation_type == violation_type]
        
        # Return most recent violations
        return sorted(violations, key=lambda v: v.timestamp, reverse=True)[:limit]
    
    def get_throughput(self, time_window_minutes: int = 5) -> float:
        """
        Calculate throughput (requests per minute).
        
        Args:
            time_window_minutes: Time window to calculate over
            
        Returns:
            Requests per minute
        """
        cutoff = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        recent_requests = [
            r for r in self.completed_requests
            if r.start_time >= cutoff
        ]
        
        if not recent_requests:
            return 0.0
        
        return len(recent_requests) / time_window_minutes
    
    def clear_old_data(self, retention_hours: int = 24) -> None:
        """
        Clear old completed requests and violations.
        
        Args:
            retention_hours: How many hours of data to retain
        """
        cutoff = datetime.utcnow() - timedelta(hours=retention_hours)
        
        # Clear old completed requests
        self.completed_requests = [
            r for r in self.completed_requests
            if r.start_time >= cutoff
        ]
        
        # Clear old violations
        self.violations = [
            v for v in self.violations
            if v.timestamp >= cutoff
        ]
        
        logger.info(
            f"Cleared performance data older than {retention_hours} hours"
        )
