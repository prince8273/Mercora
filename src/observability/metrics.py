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

        # Plain-Python summary stats (always available, no Prometheus needed)
        self._started_at: datetime = datetime.utcnow()
        self._agent_stats: Dict[str, Dict] = {}   # agent_type -> {total, success, failure, total_time}
        self._api_stats: Dict[str, Dict] = {}      # endpoint -> {total, errors, total_time}
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._query_count: int = 0
        self._active_queries: int = 0
        self._llm_tokens: int = 0
        self._llm_prompt_tokens: int = 0
        self._llm_completion_tokens: int = 0
        self._llm_cost_usd: float = 0.0
        self._llm_calls: int = 0
        
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
        # Always update plain stats
        s = self._agent_stats.setdefault(metrics.agent_type, {
            'total': 0, 'success': 0, 'failure': 0, 'total_time': 0.0
        })
        s['total'] += 1
        s['total_time'] += metrics.execution_time_seconds
        if metrics.status == 'success':
            s['success'] += 1
        else:
            s['failure'] += 1

        if not self.enabled:
            return
        try:
            self.agent_execution_time.labels(
                agent_type=metrics.agent_type,
                status=metrics.status
            ).observe(metrics.execution_time_seconds)
            self.agent_executions_total.labels(
                agent_type=metrics.agent_type,
                status=metrics.status
            ).inc()
            if metrics.cpu_usage_percent is not None:
                self.agent_cpu_usage.labels(agent_type=metrics.agent_type).set(metrics.cpu_usage_percent)
            if metrics.memory_usage_mb is not None:
                self.agent_memory_usage.labels(agent_type=metrics.agent_type).set(metrics.memory_usage_mb)
        except Exception as e:
            logger.error(f"Failed to record agent metrics: {e}")
    
    def record_api_request(self, metrics: APIMetrics) -> None:
        """Record metrics for an API request."""
        # Always update plain stats
        s = self._api_stats.setdefault(metrics.endpoint, {
            'total': 0, 'errors': 0, 'total_time': 0.0
        })
        s['total'] += 1
        s['total_time'] += metrics.response_time_seconds
        if metrics.status_code >= 400:
            s['errors'] += 1

        if not self.enabled:
            return
        try:
            self.api_request_duration.labels(
                endpoint=metrics.endpoint,
                method=metrics.method,
                status_code=str(metrics.status_code)
            ).observe(metrics.response_time_seconds)
            self.api_requests_total.labels(
                endpoint=metrics.endpoint,
                method=metrics.method,
                status_code=str(metrics.status_code)
            ).inc()
            if metrics.request_size_bytes is not None:
                self.api_request_size.labels(endpoint=metrics.endpoint, method=metrics.method).observe(metrics.request_size_bytes)
            if metrics.response_size_bytes is not None:
                self.api_response_size.labels(endpoint=metrics.endpoint, method=metrics.method).observe(metrics.response_size_bytes)
        except Exception as e:
            logger.error(f"Failed to record API metrics: {e}")
    
    def increment_active_queries(self) -> None:
        self._active_queries += 1
        self._query_count += 1
        if self.enabled:
            self.active_queries.inc()
    
    def decrement_active_queries(self) -> None:
        self._active_queries = max(0, self._active_queries - 1)
        if self.enabled:
            self.active_queries.dec()
    
    def record_cache_hit(self, cache_type: str = "query") -> None:
        self._cache_hits += 1
        if self.enabled:
            self.cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str = "query") -> None:
        self._cache_misses += 1
        if self.enabled:
            self.cache_misses.labels(cache_type=cache_type).inc()
    
    def record_llm_tokens(self, tokens: int, model: str, operation: str = "completion",
                          prompt_tokens: int = 0, completion_tokens: int = 0,
                          cost_usd: float = 0.0) -> None:
        """Record LLM token usage."""
        self._llm_tokens += tokens
        self._llm_prompt_tokens += prompt_tokens
        self._llm_completion_tokens += completion_tokens
        self._llm_cost_usd += cost_usd
        self._llm_calls += 1
        if self.enabled:
            self.llm_tokens_used.labels(model=model, operation=operation).inc(tokens)
    
    def set_data_quality_score(self, score: float, tenant_id: str) -> None:
        """Set the current data quality score for a tenant."""
        if self.enabled and 0 <= score <= 1:
            self.data_quality_score.labels(tenant_id=tenant_id).set(score)
    
    def get_summary(self) -> dict:
        """Return a human-readable JSON summary of collected stats."""
        uptime_seconds = (datetime.utcnow() - self._started_at).total_seconds()

        # Agent breakdown
        agents = []
        for agent_type, s in self._agent_stats.items():
            total = s['total']
            avg_time = round(s['total_time'] / total, 3) if total > 0 else 0
            success_rate = round(s['success'] / total * 100, 1) if total > 0 else 0
            agents.append({
                'agent': agent_type,
                'total_executions': total,
                'success': s['success'],
                'failure': s['failure'],
                'success_rate_pct': success_rate,
                'avg_execution_time_s': avg_time,
            })

        # API breakdown (top 10 by call count)
        api_endpoints = []
        for endpoint, s in sorted(self._api_stats.items(), key=lambda x: -x[1]['total'])[:10]:
            total = s['total']
            avg_time = round(s['total_time'] / total * 1000, 1) if total > 0 else 0  # ms
            error_rate = round(s['errors'] / total * 100, 1) if total > 0 else 0
            api_endpoints.append({
                'endpoint': endpoint,
                'total_requests': total,
                'errors': s['errors'],
                'error_rate_pct': error_rate,
                'avg_response_time_ms': avg_time,
            })

        # Cache
        total_cache = self._cache_hits + self._cache_misses
        cache_hit_rate = round(self._cache_hits / total_cache * 100, 1) if total_cache > 0 else 0

        return {
            'uptime_seconds': round(uptime_seconds),
            'started_at': self._started_at.isoformat(),
            'queries': {
                'total': self._query_count,
                'active': self._active_queries,
            },
            'cache': {
                'hits': self._cache_hits,
                'misses': self._cache_misses,
                'hit_rate_pct': cache_hit_rate,
            },
            'llm': {
                'calls': self._llm_calls,
                'total_tokens': self._llm_tokens,
                'prompt_tokens': self._llm_prompt_tokens,
                'completion_tokens': self._llm_completion_tokens,
                'estimated_cost_usd': round(self._llm_cost_usd, 4),
            },
            'agents': agents,
            'api_endpoints': api_endpoints,
        }

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
