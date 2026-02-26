"""
LLM Reasoning Engine - Production-Ready Version with Refinements

Improvements over v1:
1. Tenant-scoped prompt caching with TTL
2. Robust JSON parsing with fallback
3. Confidence tracking in execution plans
4. Configurable token cost per model
5. Rate limiting and circuit breaker
"""
import logging
import json
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum
from collections import deque

from src.config import settings

logger = logging.getLogger(__name__)


# Import existing classes
from src.orchestration.llm_reasoning_engine import (
    AgentType,
    ExecutionMode,
    QueryIntent,
    ExecutionPlan,
    TokenUsage
)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for LLM API calls.
    
    Prevents cascading failures by:
    - Opening circuit after N consecutive failures
    - Rejecting requests when open
    - Testing recovery in half-open state
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN - too many failures")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.success_count = 0
                logger.info("Circuit breaker CLOSED - service recovered")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.error(f"Circuit breaker OPEN after {self.failure_count} failures")


class RateLimiter:
    """
    Token bucket rate limiter for LLM API calls.
    
    Prevents:
    - Exceeding API rate limits
    - Runaway loops
    - Cost overruns
    """
    
    def __init__(self, max_calls_per_minute: int = 60):
        self.max_calls_per_minute = max_calls_per_minute
        self.calls = deque()
    
    def acquire(self) -> bool:
        """
        Attempt to acquire permission for API call.
        
        Returns:
            True if allowed, False if rate limit exceeded
        """
        now = time.time()
        
        # Remove calls older than 1 minute
        while self.calls and self.calls[0] < now - 60:
            self.calls.popleft()
        
        # Check if under limit
        if len(self.calls) < self.max_calls_per_minute:
            self.calls.append(now)
            return True
        
        return False
    
    def wait_time(self) -> float:
        """Get seconds to wait before next call is allowed"""
        if len(self.calls) < self.max_calls_per_minute:
            return 0.0
        
        oldest_call = self.calls[0]
        wait_until = oldest_call + 60
        return max(0.0, wait_until - time.time())


class TenantScopedCache:
    """
    Tenant-scoped prompt cache with TTL.
    
    Improvements over v1:
    - Tenant isolation in cache keys
    - Time-based expiration
    - Size limits
    """
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, tenant_id: UUID, query: str) -> Optional[Any]:
        """Get cached value with tenant isolation"""
        cache_key = self._generate_key(tenant_id, query)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Check expiration
            if datetime.utcnow() - entry["timestamp"] < timedelta(seconds=self.ttl_seconds):
                logger.debug(f"Cache hit for tenant {tenant_id}")
                return entry["value"]
            else:
                # Expired
                del self.cache[cache_key]
        
        return None
    
    def set(self, tenant_id: UUID, query: str, value: Any):
        """Set cached value with tenant isolation"""
        # Enforce size limit (LRU eviction)
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
        
        cache_key = self._generate_key(tenant_id, query)
        self.cache[cache_key] = {
            "value": value,
            "timestamp": datetime.utcnow()
        }
    
    def _generate_key(self, tenant_id: UUID, query: str) -> str:
        """Generate tenant-scoped cache key"""
        import hashlib
        combined = f"{tenant_id}:{query.lower().strip()}"
        return hashlib.md5(combined.encode()).hexdigest()


class ModelCostConfig:
    """
    Configurable token cost per model.
    
    Supports:
    - Multiple models
    - Different input/output costs
    - Easy updates
    """
    
    COSTS = {
        "gpt-4": {
            "input_per_1k": 0.03,
            "output_per_1k": 0.06
        },
        "gpt-4-turbo": {
            "input_per_1k": 0.01,
            "output_per_1k": 0.03
        },
        "gpt-3.5-turbo": {
            "input_per_1k": 0.0015,
            "output_per_1k": 0.002
        },
        "gemini-pro": {
            "input_per_1k": 0.00025,
            "output_per_1k": 0.0005
        },
        "gemini-2.0-flash": {
            "input_per_1k": 0.0001,
            "output_per_1k": 0.0002
        }
    }
    
    @classmethod
    def get_cost(cls, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for token usage"""
        costs = cls.COSTS.get(model, cls.COSTS["gpt-4"])  # Default to GPT-4
        
        input_cost = (prompt_tokens / 1000) * costs["input_per_1k"]
        output_cost = (completion_tokens / 1000) * costs["output_per_1k"]
        
        return input_cost + output_cost


class EnhancedTokenUsage(TokenUsage):
    """Enhanced token usage with model-specific costs"""
    
    def __init__(self, model: str = "gpt-4"):
        super().__init__()
        self.model = model
    
    def add_usage(self, prompt_tokens: int, completion_tokens: int):
        """Add token usage with accurate cost calculation"""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += (prompt_tokens + completion_tokens)
        
        # Calculate cost using model-specific pricing
        cost = ModelCostConfig.get_cost(self.model, prompt_tokens, completion_tokens)
        self.estimated_cost_usd += cost


class EnhancedExecutionPlan(ExecutionPlan):
    """Enhanced execution plan with confidence tracking"""
    
    def __init__(self, *args, query_confidence: float = 1.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_confidence = query_confidence  # LLM's confidence in understanding query
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with confidence"""
        result = super().to_dict()
        result["query_confidence"] = self.query_confidence
        return result


def extract_json_robust(response: str) -> Dict[str, Any]:
    """
    Robust JSON extraction from LLM response.
    
    Handles:
    - Markdown code blocks
    - Extra text before/after JSON
    - Malformed responses
    """
    # Try direct parsing first
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    
    # Remove markdown code blocks
    response = re.sub(r'```json\s*', '', response)
    response = re.sub(r'```\s*', '', response)
    
    # Try again
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    
    # Extract first { to last }
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Give up
    raise ValueError(f"Could not extract valid JSON from response: {response[:200]}...")


# Export enhanced classes
__all__ = [
    'CircuitBreaker',
    'RateLimiter',
    'TenantScopedCache',
    'ModelCostConfig',
    'EnhancedTokenUsage',
    'EnhancedExecutionPlan',
    'extract_json_robust'
]
