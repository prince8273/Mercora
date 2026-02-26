"""
Metrics Collection for E-commerce Intelligence Agent

Provides Prometheus-compatible metrics for monitoring system health and performance.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time
from typing import Callable, Any


# Request Metrics
request_count = Counter(
    'ecommerce_agent_requests_total',
    'Total number of requests',
    ['endpoint', 'method', 'status']
)

request_duration = Histogram(
    'ecommerce_agent_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint', 'method']
)

# Query Metrics
query_count = Counter(
    'ecommerce_agent_queries_total',
    'Total number of queries processed',
    ['execution_mode', 'status']
)

query_duration = Histogram(
    'ecommerce_agent_query_duration_seconds',
    'Query execution duration in seconds',
    ['execution_mode']
)

# Agent Metrics
agent_execution_count = Counter(
    'ecommerce_agent_executions_total',
    'Total number of agent executions',
    ['agent_type', 'status']
)

agent_execution_duration = Histogram(
    'ecommerce_agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_type']
)

agent_confidence = Histogram(
    'ecommerce_agent_confidence_score',
    'Agent confidence scores',
    ['agent_type'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# LLM Metrics
llm_token_usage = Counter(
    'ecommerce_agent_llm_tokens_total',
    'Total LLM tokens used',
    ['token_type', 'provider']  # token_type: prompt, response, total
)

llm_request_count = Counter(
    'ecommerce_agent_llm_requests_total',
    'Total LLM API requests',
    ['provider', 'status']
)

llm_request_duration = Histogram(
    'ecommerce_agent_llm_request_duration_seconds',
    'LLM API request duration',
    ['provider']
)

# Database Metrics
db_query_count = Counter(
    'ecommerce_agent_db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration = Histogram(
    'ecommerce_agent_db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

# Cache Metrics
cache_hit_count = Counter(
    'ecommerce_agent_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_miss_count = Counter(
    'ecommerce_agent_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

cache_size = Gauge(
    'ecommerce_agent_cache_size_bytes',
    'Current cache size in bytes',
    ['cache_type']
)

# Data Metrics
data_ingestion_count = Counter(
    'ecommerce_agent_data_ingested_total',
    'Total data records ingested',
    ['data_type', 'source']
)

data_validation_errors = Counter(
    'ecommerce_agent_validation_errors_total',
    'Total data validation errors',
    ['data_type', 'error_type']
)

# System Metrics
active_users = Gauge(
    'ecommerce_agent_active_users',
    'Number of active users'
)

active_tenants = Gauge(
    'ecommerce_agent_active_tenants',
    'Number of active tenants'
)

# Application Info
app_info = Info(
    'ecommerce_agent_app',
    'Application information'
)


def track_request_metrics(endpoint: str, method: str):
    """Decorator to track request metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                request_count.labels(
                    endpoint=endpoint,
                    method=method,
                    status=status
                ).inc()
                request_duration.labels(
                    endpoint=endpoint,
                    method=method
                ).observe(duration)
        
        return wrapper
    return decorator


def track_query_metrics(execution_mode: str):
    """Decorator to track query execution metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                query_count.labels(
                    execution_mode=execution_mode,
                    status=status
                ).inc()
                query_duration.labels(
                    execution_mode=execution_mode
                ).observe(duration)
        
        return wrapper
    return decorator


def track_agent_metrics(agent_type: str):
    """Decorator to track agent execution metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                
                # Track confidence if available
                if hasattr(result, 'confidence'):
                    agent_confidence.labels(
                        agent_type=agent_type
                    ).observe(result.confidence)
                
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                agent_execution_count.labels(
                    agent_type=agent_type,
                    status=status
                ).inc()
                agent_execution_duration.labels(
                    agent_type=agent_type
                ).observe(duration)
        
        return wrapper
    return decorator


def track_llm_metrics(provider: str):
    """Track LLM API call metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                
                # Track token usage if available
                if hasattr(result, 'usage'):
                    llm_token_usage.labels(
                        token_type='prompt',
                        provider=provider
                    ).inc(result.usage.get('prompt_tokens', 0))
                    
                    llm_token_usage.labels(
                        token_type='response',
                        provider=provider
                    ).inc(result.usage.get('completion_tokens', 0))
                    
                    llm_token_usage.labels(
                        token_type='total',
                        provider=provider
                    ).inc(result.usage.get('total_tokens', 0))
                
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                llm_request_count.labels(
                    provider=provider,
                    status=status
                ).inc()
                llm_request_duration.labels(
                    provider=provider
                ).observe(duration)
        
        return wrapper
    return decorator


def track_db_metrics(operation: str, table: str):
    """Track database operation metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                db_query_count.labels(
                    operation=operation,
                    table=table
                ).inc()
                db_query_duration.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
        
        return wrapper
    return decorator


def track_cache_hit(cache_type: str = "query"):
    """Track cache hit"""
    cache_hit_count.labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str = "query"):
    """Track cache miss"""
    cache_miss_count.labels(cache_type=cache_type).inc()


def update_cache_size(size_bytes: int, cache_type: str = "query"):
    """Update cache size gauge"""
    cache_size.labels(cache_type=cache_type).set(size_bytes)


def track_data_ingestion(data_type: str, source: str, count: int = 1):
    """Track data ingestion"""
    data_ingestion_count.labels(
        data_type=data_type,
        source=source
    ).inc(count)


def track_validation_error(data_type: str, error_type: str):
    """Track validation error"""
    data_validation_errors.labels(
        data_type=data_type,
        error_type=error_type
    ).inc()


def update_active_users(count: int):
    """Update active users gauge"""
    active_users.set(count)


def update_active_tenants(count: int):
    """Update active tenants gauge"""
    active_tenants.set(count)


def initialize_app_info(name: str, version: str, environment: str):
    """Initialize application info"""
    app_info.info({
        'name': name,
        'version': version,
        'environment': environment
    })
