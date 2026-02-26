"""Prometheus metrics collection for agents and API endpoints."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List
from uuid import UUID
from enum import Enum

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback stubs for when prometheus_client is not installed
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class CollectorRegistry:
        def __init__(self, *args, **kwargs): pass
    
    def generate_latest(*args, **kwargs): return b""
    CONTENT_TYPE_LATEST = "text/plain"


logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Agent types for metrics labeling."""
    PRICING = "pricing"
    SENTIMENT = "sentiment"
    FORECAST = "forecast"
    CUSTOM = "custom"


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution."""
    agent_type: str
    execution_time_seconds: float
    cpu_usage_percent: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    status: str = "success"  # success, failure, partial
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class APIMetrics:
    """Metrics for API endpoint requests."""
    endpoint: str
    method: str
    status_code: int
    response_time_seconds: float
    request_size_bytes: Optional[int] = None
    response_size_bytes: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:
    """
    Prometheus metrics collector for agents and API endpoints.
    
    Collects:
    - Agent execution time, resource usage, success/failure rates
    - API endpoint response time, throughput, error rates
    - Custom business KPIs
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics collector with optional custom registry."""
        self.registry = registry or CollectorRegistry()
        self.enabled = PROMETHEUS_AVAILABLE
        
        if not self.enabled:
            logger.warning(
                "Prometheus client not installed. Metrics collection disabled. "
                "Install with: pip install prometheus-client"
            )
        
        # Agent metrics
        self.agent_execution_time = Histogram(
            'agent_execution_seconds',
            'Agent execution time in seconds',
            ['agent_type', 'status'],
            registry=self.registry,
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
        )
        
        self.agent_executions_total = Counter(
            'agent_executions_total',
            'Total number of agent executions',
            ['agent_type', 'status'],
            registry=self.registry
        )
        
        self.agent_cpu_usage = Gauge(
            'agent_cpu_usage_percent',
            'Agent CPU usage percentage',
            ['agent_type'],
            registry=self.registry
        )
        
        self.agent_memory_usage = Gauge(
            'agent_memory_usage_mb',
            'Agent memory usage in MB',
            ['agent_type'],
            registry=self.registry
        )
        
        # API metrics
        self.api_request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration in seconds',
            ['endpoint', 'method', 'status_code'],
            registry=self.registry,
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
        
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total number of API requests',
            ['endpoint', 'method', 'status_code'],
            registry=self.registry
        )
        
        self.api_request_size = Summary(
            'api_request_size_bytes',
            'API request size in bytes',
            ['endpoint', 'method'],
            registry=self.registry
        )
        
        self.api_response_size = Summary(
            'api_response_size_bytes',
            'API response size in bytes',
            ['endpoint', 'method'],
            registry=self.registry
        )
        
        # Business KPIs
        self.active_queries = Gauge(
            'active_queries_total',
            'Number of currently active queries',
            registry=self.registry
        )
        
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total number of cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total number of cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        self.llm_tokens_used = Counter(
            'llm_tokens_used_total',
            'Total number of LLM tokens used',
            ['model', 'operation'],
            registry=self.registry
        )
        
        self.data_quality_score = Gauge(
            'data_quality_score',
            'Current data quality score (0-1)',
            ['tenant_id'],
            registry=self.registry
        )
        
        logger.info("MetricsCollector initialized")
    
    def record_agent_execution(self, metrics: AgentMetrics) -> None:
        """Record metrics for an agent execution."""
        if not self.enabled:
            return
        
        try:
            # Record execution time
            self.agent_execution_time.labels(
                agent_type=metrics.agent_type,
                status=metrics.status
            ).observe(metrics.execution_time_seconds)
            
            # Increment execution counter
            self.agent_executions_total.labels(
                agent_type=metrics.agent_type,
                status=metrics.status
            ).inc()
            
            # Record resource usage if available
            if metrics.cpu_usage_percent is not None:
                self.agent_cpu_usage.labels(
                    agent_type=metrics.agent_type
                ).set(metrics.cpu_usage_percent)
            
            if metrics.memory_usage_mb is not None:
                self.agent_memory_usage.labels(
                    agent_type=metrics.agent_type
                ).set(metrics.memory_usage_mb)
            
            logger.debug(
                f"Recorded agent metrics: {metrics.agent_type} "
                f"({metrics.execution_time_seconds:.2f}s, {metrics.status})"
            )
        except Exception as e:
            logger.error(f"Failed to record agent metrics: {e}")
    
    def record_api_request(self, metrics: APIMetrics) -> None:
        """Record metrics for an API request."""
        if not self.enabled:
            return
        
        try:
            # Record request duration
            self.api_request_duration.labels(
                endpoint=metrics.endpoint,
                method=metrics.method,
                status_code=str(metrics.status_code)
            ).observe(metrics.response_time_seconds)
            
            # Increment request counter
            self.api_requests_total.labels(
                endpoint=metrics.endpoint,
                method=metrics.method,
                status_code=str(metrics.status_code)
            ).inc()
            
            # Record request/response sizes if available
            if metrics.request_size_bytes is not None:
                self.api_request_size.labels(
                    endpoint=metrics.endpoint,
                    method=metrics.method
                ).observe(metrics.request_size_bytes)
            
            if metrics.response_size_bytes is not None:
                self.api_response_size.labels(
                    endpoint=metrics.endpoint,
                    method=metrics.method
                ).observe(metrics.response_size_bytes)
            
            logger.debug(
                f"Recorded API metrics: {metrics.method} {metrics.endpoint} "
                f"({metrics.status_code}, {metrics.response_time_seconds:.3f}s)"
            )
        except Exception as e:
            logger.error(f"Failed to record API metrics: {e}")
    
    def increment_active_queries(self) -> None:
        """Increment the count of active queries."""
        if self.enabled:
            self.active_queries.inc()
    
    def decrement_active_queries(self) -> None:
        """Decrement the count of active queries."""
        if self.enabled:
            self.active_queries.dec()
    
    def record_cache_hit(self, cache_type: str = "query") -> None:
        """Record a cache hit."""
        if self.enabled:
            self.cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str = "query") -> None:
        """Record a cache miss."""
        if self.enabled:
            self.cache_misses.labels(cache_type=cache_type).inc()
    
    def record_llm_tokens(self, tokens: int, model: str, operation: str = "completion") -> None:
        """Record LLM token usage."""
        if self.enabled:
            self.llm_tokens_used.labels(model=model, operation=operation).inc(tokens)
    
    def set_data_quality_score(self, score: float, tenant_id: str) -> None:
        """Set the current data quality score for a tenant."""
        if self.enabled and 0 <= score <= 1:
            self.data_quality_score.labels(tenant_id=tenant_id).set(score)
    
    def get_metrics(self) -> bytes:
        """Get current metrics in Prometheus format."""
        if not self.enabled:
            return b""
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get the content type for metrics endpoint."""
        return CONTENT_TYPE_LATEST


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
