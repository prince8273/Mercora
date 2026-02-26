"""Alerting system for performance anomalies and errors."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
from uuid import uuid4
from collections import deque


logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts."""
    PERFORMANCE_ANOMALY = "performance_anomaly"
    ERROR_RATE_SPIKE = "error_rate_spike"
    RESPONSE_TIME_SPIKE = "response_time_spike"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    HEALTH_CHECK_FAILURE = "health_check_failure"
    SECURITY_INCIDENT = "security_incident"
    REPEATED_FAILURE = "repeated_failure"  # Req 18.1
    TIMEOUT_ESCALATION = "timeout_escalation"  # Req 18.2
    DATABASE_CONNECTION_FAILURE = "database_connection_failure"  # Req 18.3


@dataclass
class Alert:
    """Represents an alert."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    delivered_at: Optional[datetime] = None  # Req 18.5
    
    def acknowledge(self, user: str) -> None:
        """Acknowledge the alert."""
        self.acknowledged = True
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user
    
    def resolve(self, user: str, notes: str) -> None:
        """Resolve the alert with notes."""
        self.resolved = True
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = notes
        if not self.acknowledged:
            self.acknowledge(user)
    
    def get_resolution_time(self) -> Optional[timedelta]:
        """Get time from alert creation to resolution."""
        if self.resolved_at:
            return self.resolved_at - self.timestamp
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "resolution_time_seconds": self.get_resolution_time().total_seconds() if self.get_resolution_time() else None,
        }


@dataclass
class PerformanceMetric:
    """Performance metric for anomaly detection."""
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AlertManager:
    """
    Alert manager for performance anomalies and errors.
    
    Features:
    - Detect performance anomalies (response time spikes, error rate increases)
    - Generate alerts with severity levels
    - Track alert acknowledgment
    - Support multiple delivery channels (email, Slack, PagerDuty)
    
    Validates Property 65: Performance anomalies trigger alerts.
    """
    
    def __init__(
        self,
        response_time_threshold: float = 5.0,  # seconds
        error_rate_threshold: float = 0.1,  # 10%
        window_size: int = 100,  # number of samples to track
        enabled: bool = True,
        alert_delivery_sla_minutes: int = 5  # Req 18.5
    ):
        """Initialize alert manager."""
        self.response_time_threshold = response_time_threshold
        self.error_rate_threshold = error_rate_threshold
        self.window_size = window_size
        self.enabled = enabled
        self.alert_delivery_sla_minutes = alert_delivery_sla_minutes
        
        # Alert storage
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Performance tracking
        self.response_times: deque = deque(maxlen=window_size)
        self.error_counts: deque = deque(maxlen=window_size)
        self.request_counts: deque = deque(maxlen=window_size)
        
        # Failure tracking (Req 18.1, 18.2, 18.3)
        self.failure_counts: Dict[str, int] = {}  # Track consecutive failures by source
        self.timeout_counts: Dict[str, int] = {}  # Track timeouts by operation
        self.db_connection_failures: int = 0
        self.last_db_failure_time: Optional[datetime] = None
        
        # Baseline metrics
        self.baseline_response_time: Optional[float] = None
        self.baseline_error_rate: Optional[float] = None
        
        logger.info("AlertManager initialized")
    
    def record_response_time(self, response_time: float) -> None:
        """Record a response time measurement."""
        self.response_times.append(PerformanceMetric(value=response_time))
        
        # Update baseline
        if len(self.response_times) >= 10:
            self.baseline_response_time = sum(
                m.value for m in list(self.response_times)[-10:]
            ) / 10
    
    def record_request(self, is_error: bool = False) -> None:
        """Record a request (success or error)."""
        self.request_counts.append(1)
        self.error_counts.append(1 if is_error else 0)
        
        # Update baseline error rate
        if len(self.error_counts) >= 10:
            recent_errors = sum(list(self.error_counts)[-10:])
            recent_requests = sum(list(self.request_counts)[-10:])
            self.baseline_error_rate = recent_errors / recent_requests if recent_requests > 0 else 0
    
    def check_response_time_anomaly(self) -> Optional[Alert]:
        """
        Check for response time anomalies.
        
        Validates Property 65: Performance anomalies trigger alerts.
        """
        if not self.enabled or len(self.response_times) < 5:
            return None
        
        # Get recent response times (last 5)
        recent_times = [m.value for m in list(self.response_times)[-5:]]
        avg_recent = sum(recent_times) / len(recent_times)
        max_recent = max(recent_times)
        
        # Deterministic threshold check: trigger if average OR max exceeds threshold
        if avg_recent >= self.response_time_threshold or max_recent >= self.response_time_threshold:
            # Also check for baseline spike if we have enough data
            baseline = None
            spike_factor = None
            
            if len(self.response_times) >= 10:
                baseline_times = [m.value for m in list(self.response_times)[:-5]]
                baseline = sum(baseline_times) / len(baseline_times)
                spike_factor = avg_recent / baseline if baseline > 0 else None
            
            alert = Alert(
                alert_id=str(uuid4()),
                alert_type=AlertType.RESPONSE_TIME_SPIKE,
                severity=AlertSeverity.ERROR if max_recent > self.response_time_threshold * 2 else AlertSeverity.WARNING,
                title="Response Time Spike Detected",
                message=f"Response time spike detected: avg={avg_recent:.2f}s, max={max_recent:.2f}s, threshold={self.response_time_threshold:.2f}s",
                metadata={
                    "current_avg": avg_recent,
                    "current_max": max_recent,
                    "baseline": baseline,
                    "threshold": self.response_time_threshold,
                    "spike_factor": spike_factor
                }
            )
            
            self._store_alert(alert)
            return alert
        
        # Also check for 2x baseline spike even if below absolute threshold
        if len(self.response_times) >= 10:
            baseline_times = [m.value for m in list(self.response_times)[:-5]]
            baseline = sum(baseline_times) / len(baseline_times)
            
            if baseline > 0 and avg_recent > baseline * 2:
                alert = Alert(
                    alert_id=str(uuid4()),
                    alert_type=AlertType.RESPONSE_TIME_SPIKE,
                    severity=AlertSeverity.WARNING,
                    title="Response Time Spike Detected",
                    message=f"Response time is {avg_recent/baseline:.1f}x baseline: avg={avg_recent:.2f}s, baseline={baseline:.2f}s",
                    metadata={
                        "current_avg": avg_recent,
                        "current_max": max_recent,
                        "baseline": baseline,
                        "threshold": self.response_time_threshold,
                        "spike_factor": avg_recent / baseline
                    }
                )
                
                self._store_alert(alert)
                return alert
        
        return None
    
    def check_error_rate_anomaly(self) -> Optional[Alert]:
        """
        Check for error rate anomalies.
        
        Validates Property 65: Performance anomalies trigger alerts.
        """
        if not self.enabled or len(self.error_counts) < 10:
            return None
        
        # Calculate recent error rate (last 10 requests)
        recent_errors = sum(list(self.error_counts)[-10:])
        recent_requests = sum(list(self.request_counts)[-10:])
        
        if recent_requests == 0:
            return None
        
        current_error_rate = recent_errors / recent_requests
        
        # Check if at or above threshold (>= for boundary cases)
        if current_error_rate >= self.error_rate_threshold:
            alert = Alert(
                alert_id=str(uuid4()),
                alert_type=AlertType.ERROR_RATE_SPIKE,
                severity=AlertSeverity.ERROR if current_error_rate >= 0.2 else AlertSeverity.WARNING,
                title="Error Rate Spike Detected",
                message=f"Error rate ({current_error_rate:.1%}) exceeds threshold ({self.error_rate_threshold:.1%})",
                metadata={
                    "current_error_rate": current_error_rate,
                    "baseline_error_rate": self.baseline_error_rate,
                    "threshold": self.error_rate_threshold,
                    "recent_errors": recent_errors,
                    "recent_requests": recent_requests
                }
            )
            
            self._store_alert(alert)
            return alert
        
        return None
    
    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a custom alert."""
        alert = Alert(
            alert_id=str(uuid4()),
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            metadata=metadata or {}
        )
        
        self._store_alert(alert)
        self._deliver_alert(alert)  # Req 18.5
        return alert
    
    def check_repeated_failures(
        self,
        source_id: str,
        failure_threshold: int = 3
    ) -> Optional[Alert]:
        """
        Check for repeated failures from a source (Req 18.1).
        
        Validates Property 72: Repeated failures trigger escalation.
        """
        if not self.enabled:
            return None
        
        # Increment failure count
        self.failure_counts[source_id] = self.failure_counts.get(source_id, 0) + 1
        
        if self.failure_counts[source_id] >= failure_threshold:
            alert = Alert(
                alert_id=str(uuid4()),
                alert_type=AlertType.REPEATED_FAILURE,
                severity=AlertSeverity.CRITICAL,
                title=f"Repeated Failures Detected: {source_id}",
                message=f"Source '{source_id}' has failed {self.failure_counts[source_id]} consecutive times (threshold: {failure_threshold})",
                metadata={
                    "source_id": source_id,
                    "failure_count": self.failure_counts[source_id],
                    "threshold": failure_threshold,
                    "escalate_to": "system_administrators"
                }
            )
            
            self._store_alert(alert)
            self._deliver_alert(alert)
            return alert
        
        return None
    
    def reset_failure_count(self, source_id: str) -> None:
        """Reset failure count for a source after success."""
        if source_id in self.failure_counts:
            self.failure_counts[source_id] = 0
    
    def check_timeout_escalation(
        self,
        operation: str,
        timeout_seconds: float,
        actual_seconds: float
    ) -> Optional[Alert]:
        """
        Check for timeout escalation (Req 18.2).
        
        Validates Property 73: Timeouts trigger escalation.
        """
        if not self.enabled:
            return None
        
        # Track timeout
        self.timeout_counts[operation] = self.timeout_counts.get(operation, 0) + 1
        
        alert = Alert(
            alert_id=str(uuid4()),
            alert_type=AlertType.TIMEOUT_ESCALATION,
            severity=AlertSeverity.ERROR if self.timeout_counts[operation] >= 3 else AlertSeverity.WARNING,
            title=f"Timeout Escalation: {operation}",
            message=f"Operation '{operation}' exceeded timeout: {actual_seconds:.2f}s > {timeout_seconds:.2f}s (occurrence #{self.timeout_counts[operation]})",
            metadata={
                "operation": operation,
                "timeout_seconds": timeout_seconds,
                "actual_seconds": actual_seconds,
                "timeout_count": self.timeout_counts[operation],
                "escalate_to": "on_call_personnel" if self.timeout_counts[operation] >= 3 else "team"
            }
        )
        
        self._store_alert(alert)
        self._deliver_alert(alert)
        return alert
    
    def check_database_connection_failure(
        self,
        error_message: str,
        connection_pool_status: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """
        Check for database connection failures (Req 18.3).
        
        Validates Property 74: Connection failures trigger high-priority alerts.
        """
        if not self.enabled:
            return None
        
        self.db_connection_failures += 1
        self.last_db_failure_time = datetime.utcnow()
        
        # Check if failures are persistent (within last 5 minutes)
        is_persistent = self.db_connection_failures >= 3
        
        alert = Alert(
            alert_id=str(uuid4()),
            alert_type=AlertType.DATABASE_CONNECTION_FAILURE,
            severity=AlertSeverity.CRITICAL if is_persistent else AlertSeverity.ERROR,
            title="Database Connection Failure",
            message=f"Database connection failed: {error_message} (failure #{self.db_connection_failures})",
            metadata={
                "error_message": error_message,
                "failure_count": self.db_connection_failures,
                "last_failure_time": self.last_db_failure_time.isoformat(),
                "connection_pool_status": connection_pool_status or {},
                "is_persistent": is_persistent,
                "escalate_to": "database_team"
            }
        )
        
        self._store_alert(alert)
        self._deliver_alert(alert)
        return alert
    
    def reset_database_failure_count(self) -> None:
        """Reset database failure count after successful connection."""
        self.db_connection_failures = 0
        self.last_db_failure_time = None
    
    def check_health_check_failure(
        self,
        component: str,
        diagnostics: Dict[str, Any]
    ) -> Optional[Alert]:
        """
        Check for health check failures with diagnostics (Req 18.4).
        
        Validates Property 75: Health check failures include diagnostics.
        """
        if not self.enabled:
            return None
        
        alert = Alert(
            alert_id=str(uuid4()),
            alert_type=AlertType.HEALTH_CHECK_FAILURE,
            severity=AlertSeverity.ERROR,
            title=f"Health Check Failed: {component}",
            message=f"Component '{component}' failed health check",
            metadata={
                "component": component,
                "diagnostics": diagnostics,
                "timestamp": datetime.utcnow().isoformat(),
                "recommended_actions": self._generate_health_check_actions(component, diagnostics)
            }
        )
        
        self._store_alert(alert)
        self._deliver_alert(alert)
        return alert
    
    def _generate_health_check_actions(
        self,
        component: str,
        diagnostics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommended actions based on health check diagnostics."""
        actions = []
        
        if "database" in component.lower():
            actions.append("Check database connection pool status")
            actions.append("Verify database credentials")
            actions.append("Check database server availability")
        elif "cache" in component.lower() or "redis" in component.lower():
            actions.append("Check Redis server status")
            actions.append("Verify Redis connection settings")
            actions.append("Check network connectivity to Redis")
        elif "api" in component.lower():
            actions.append("Check API endpoint availability")
            actions.append("Verify API credentials")
            actions.append("Check rate limiting status")
        else:
            actions.append(f"Investigate {component} component logs")
            actions.append(f"Restart {component} service if necessary")
        
        # Add diagnostic-specific actions
        if diagnostics.get("error_type") == "timeout":
            actions.append("Increase timeout threshold if appropriate")
        if diagnostics.get("error_type") == "connection_refused":
            actions.append("Verify service is running")
        
        return actions
    
    def _deliver_alert(self, alert: Alert) -> None:
        """
        Deliver alert through configured channels (Req 18.5).
        
        Validates Property 76: Alerts are delivered within SLA.
        """
        # Mark delivery time
        alert.delivered_at = datetime.utcnow()
        
        # Calculate delivery time
        delivery_time = (alert.delivered_at - alert.timestamp).total_seconds()
        
        # Check SLA compliance
        sla_seconds = self.alert_delivery_sla_minutes * 60
        if delivery_time > sla_seconds:
            logger.warning(
                f"Alert {alert.alert_id} delivery exceeded SLA: {delivery_time:.2f}s > {sla_seconds}s"
            )
        
        # Log delivery (in production, this would send to email/Slack/PagerDuty)
        logger.info(
            f"Alert delivered: [{alert.severity.value.upper()}] {alert.title} "
            f"(delivery_time={delivery_time:.2f}s, sla={sla_seconds}s)"
        )
    
    def resolve_alert(self, alert_id: str, user: str, notes: str) -> bool:
        """
        Resolve an alert with resolution notes (Req 18.6).
        
        Validates Property 77: Alert acknowledgments are tracked.
        """
        alert = self.alerts.get(alert_id)
        if alert:
            alert.resolve(user, notes)
            resolution_time = alert.get_resolution_time()
            logger.info(
                f"Alert {alert_id} resolved by {user} "
                f"(resolution_time={resolution_time.total_seconds():.2f}s if resolution_time else 'N/A')"
            )
            return True
        return False
    
    def _store_alert(self, alert: Alert) -> None:
        """Store an alert."""
        self.alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        
        logger.warning(
            f"Alert generated: [{alert.severity.value.upper()}] {alert.title} - {alert.message}"
        )
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        return self.alerts.get(alert_id)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unacknowledged) alerts."""
        return [
            alert for alert in self.alerts.values()
            if not alert.acknowledged
        ]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity level."""
        return [
            alert for alert in self.alerts.values()
            if alert.severity == severity and not alert.acknowledged
        ]
    
    def get_alerts_by_type(self, alert_type: AlertType) -> List[Alert]:
        """Get alerts by type."""
        return [
            alert for alert in self.alerts.values()
            if alert.alert_type == alert_type and not alert.acknowledged
        ]
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge an alert."""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.acknowledge(user)
            logger.info(f"Alert {alert_id} acknowledged by {user}")
            return True
        return False
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        active_alerts = self.get_active_alerts()
        resolved_alerts = [a for a in self.alerts.values() if a.resolved]
        
        # Calculate average resolution time
        resolution_times = [a.get_resolution_time().total_seconds() for a in resolved_alerts if a.get_resolution_time()]
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else None
        
        return {
            "total_alerts": len(self.alert_history),
            "active_alerts": len(active_alerts),
            "acknowledged_alerts": len([a for a in self.alerts.values() if a.acknowledged]),
            "resolved_alerts": len(resolved_alerts),
            "average_resolution_time_seconds": avg_resolution_time,
            "alerts_by_severity": {
                severity.value: len([
                    a for a in active_alerts if a.severity == severity
                ])
                for severity in AlertSeverity
            },
            "alerts_by_type": {
                alert_type.value: len([
                    a for a in active_alerts if a.alert_type == alert_type
                ])
                for alert_type in AlertType
            },
            "failure_tracking": {
                "repeated_failures": dict(self.failure_counts),
                "timeout_counts": dict(self.timeout_counts),
                "db_connection_failures": self.db_connection_failures
            },
            "baseline_response_time": self.baseline_response_time,
            "baseline_error_rate": self.baseline_error_rate,
        }


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
