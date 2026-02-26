"""
Graceful Degradation - Fallback Strategies

This module implements graceful degradation strategies for handling failures:
- Partial results with warnings
- Cached fallback for API failures
- Simplified model fallback
- Quick Mode fallback from Deep Mode
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

from src.error_handling.error_response import ErrorResponse, ErrorResponseFactory, ErrorCode
from src.schemas.orchestration import ExecutionMode, AgentType

logger = logging.getLogger(__name__)


class FallbackStrategy(str, Enum):
    """Fallback strategies for error handling"""
    PARTIAL_RESULTS = "partial_results"
    CACHED_DATA = "cached_data"
    SIMPLIFIED_MODEL = "simplified_model"
    QUICK_MODE = "quick_mode"
    SKIP_AGENT = "skip_agent"


class DegradationResult:
    """Result of graceful degradation"""
    
    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[ErrorResponse]] = None,
        fallback_used: Optional[FallbackStrategy] = None,
        degraded: bool = False
    ):
        self.success = success
        self.data = data or {}
        self.warnings = warnings or []
        self.fallback_used = fallback_used
        self.degraded = degraded
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "data": self.data,
            "warnings": [w.to_dict() for w in self.warnings],
            "fallback_used": self.fallback_used.value if self.fallback_used else None,
            "degraded": self.degraded
        }


class GracefulDegradationHandler:
    """
    Handles graceful degradation for various failure scenarios.
    
    Implements fallback strategies to ensure partial functionality
    even when components fail.
    """
    
    def __init__(self, cache_manager=None):
        """
        Initialize graceful degradation handler.
        
        Args:
            cache_manager: Optional cache manager for cached fallback
        """
        self.cache_manager = cache_manager
        logger.info("GracefulDegradationHandler initialized")
    
    def handle_partial_results(
        self,
        successful_agents: List[str],
        failed_agents: List[str],
        results: Dict[str, Any],
        errors: Dict[str, Exception]
    ) -> DegradationResult:
        """
        Handle partial results when some agents succeed and others fail.
        
        Args:
            successful_agents: List of successful agent names
            failed_agents: List of failed agent names
            results: Results from successful agents
            errors: Errors from failed agents
            
        Returns:
            DegradationResult with partial results and warnings
        """
        logger.info(f"Handling partial results: {len(successful_agents)} succeeded, {len(failed_agents)} failed")
        
        warnings = []
        for agent in failed_agents:
            error = errors.get(agent)
            warning = ErrorResponseFactory.agent_execution_failed(
                agent_type=agent,
                error_message=str(error) if error else "Unknown error",
                partial_results_available=len(successful_agents) > 0
            )
            warnings.append(warning)
        
        # Add data quality warning about missing agent results
        if failed_agents:
            warnings.append(ErrorResponse(
                error_code=ErrorCode.DATA_QUALITY_WARNING,
                message=f"Analysis incomplete: {len(failed_agents)} agent(s) failed",
                suggested_action=f"Results are based on {len(successful_agents)} successful agent(s) only",
                context={
                    "successful_agents": successful_agents,
                    "failed_agents": failed_agents
                },
                recoverable=True
            ))
        
        return DegradationResult(
            success=len(successful_agents) > 0,
            data=results,
            warnings=warnings,
            fallback_used=FallbackStrategy.PARTIAL_RESULTS,
            degraded=True
        )
    
    def handle_api_failure_with_cache(
        self,
        service: str,
        cache_key: str,
        retry_count: int,
        max_cache_age_hours: int = 24
    ) -> DegradationResult:
        """
        Handle API failure by falling back to cached data.
        
        Args:
            service: Name of the failed service
            cache_key: Cache key to retrieve fallback data
            retry_count: Number of retry attempts made
            max_cache_age_hours: Maximum age of cached data to use
            
        Returns:
            DegradationResult with cached data or failure
        """
        logger.warning(f"API failure for {service}, attempting cached fallback")
        
        if not self.cache_manager:
            logger.error("No cache manager available for fallback")
            return DegradationResult(
                success=False,
                warnings=[ErrorResponseFactory.api_failure(service, retry_count, False)]
            )
        
        try:
            cached_result = self.cache_manager.get(cache_key)
            
            if cached_result:
                # Check cache age
                cached_at = cached_result.get("cached_at")
                if cached_at:
                    cache_age = datetime.utcnow() - datetime.fromisoformat(cached_at)
                    if cache_age > timedelta(hours=max_cache_age_hours):
                        logger.warning(f"Cached data too old: {cache_age}")
                        return DegradationResult(
                            success=False,
                            warnings=[ErrorResponse(
                                error_code=ErrorCode.STALE_DATA,
                                message=f"Cached data is too old ({cache_age})",
                                suggested_action="Wait for service recovery or accept stale data",
                                recoverable=False
                            )]
                        )
                
                logger.info(f"Using cached data for {service}")
                return DegradationResult(
                    success=True,
                    data=cached_result.get("data", {}),
                    warnings=[ErrorResponse(
                        error_code=ErrorCode.DATA_QUALITY_WARNING,
                        message=f"Using cached data due to {service} failure",
                        suggested_action="Data may be outdated, retry later for fresh results",
                        context={"cached_at": cached_at},
                        recoverable=True
                    )],
                    fallback_used=FallbackStrategy.CACHED_DATA,
                    degraded=True
                )
            else:
                logger.error(f"No cached data available for {service}")
                return DegradationResult(
                    success=False,
                    warnings=[ErrorResponseFactory.api_failure(service, retry_count, False)]
                )
                
        except Exception as e:
            logger.error(f"Cache fallback failed: {e}")
            return DegradationResult(
                success=False,
                warnings=[
                    ErrorResponseFactory.api_failure(service, retry_count, False),
                    ErrorResponse.from_exception(e, ErrorCode.CACHE_ERROR)
                ]
            )
    
    def handle_model_failure_with_simplified_fallback(
        self,
        model_name: str,
        input_data: Dict[str, Any],
        error: Exception
    ) -> DegradationResult:
        """
        Handle model inference failure by using simplified fallback logic.
        
        Args:
            model_name: Name of the failed model
            input_data: Input data for the model
            error: Exception that occurred
            
        Returns:
            DegradationResult with simplified results
        """
        logger.warning(f"Model {model_name} failed, using simplified fallback")
        
        # Implement simplified fallback logic based on model type
        simplified_result = self._get_simplified_result(model_name, input_data)
        
        if simplified_result:
            return DegradationResult(
                success=True,
                data=simplified_result,
                warnings=[ErrorResponse(
                    error_code=ErrorCode.MODEL_INFERENCE_FAILED,
                    message=f"Model {model_name} failed, using simplified logic",
                    suggested_action="Results may be less accurate, check model health",
                    context={"model_name": model_name, "error": str(error)},
                    recoverable=True
                )],
                fallback_used=FallbackStrategy.SIMPLIFIED_MODEL,
                degraded=True
            )
        else:
            return DegradationResult(
                success=False,
                warnings=[ErrorResponse.from_exception(
                    error,
                    ErrorCode.MODEL_INFERENCE_FAILED,
                    "Check model configuration and retry"
                )]
            )
    
    def handle_deep_mode_timeout_with_quick_mode(
        self,
        query: str,
        timeout_seconds: int,
        partial_results: Optional[Dict[str, Any]] = None
    ) -> DegradationResult:
        """
        Handle Deep Mode timeout by suggesting Quick Mode fallback.
        
        Args:
            query: Original query
            timeout_seconds: Timeout that was exceeded
            partial_results: Any partial results available
            
        Returns:
            DegradationResult with fallback suggestion
        """
        logger.warning(f"Deep Mode timeout after {timeout_seconds}s, suggesting Quick Mode")
        
        if partial_results:
            return DegradationResult(
                success=True,
                data=partial_results,
                warnings=[ErrorResponse(
                    error_code=ErrorCode.TIMEOUT_EXCEEDED,
                    message="Deep Mode analysis incomplete due to timeout",
                    suggested_action="Partial results available, or retry with Quick Mode for faster response",
                    context={
                        "timeout_seconds": timeout_seconds,
                        "mode": "Deep",
                        "fallback_mode": "Quick"
                    },
                    recoverable=True
                )],
                fallback_used=FallbackStrategy.QUICK_MODE,
                degraded=True
            )
        else:
            return DegradationResult(
                success=False,
                warnings=[ErrorResponseFactory.timeout_exceeded(
                    operation="Deep Mode analysis",
                    timeout_seconds=timeout_seconds,
                    mode="Deep"
                )]
            )
    
    def _get_simplified_result(
        self,
        model_name: str,
        input_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get simplified result using rule-based logic.
        
        Args:
            model_name: Name of the model
            input_data: Input data
            
        Returns:
            Simplified result or None
        """
        # Implement simplified logic based on model type
        if "sentiment" in model_name.lower():
            # Simple sentiment fallback: neutral sentiment
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "note": "Simplified fallback result"
            }
        elif "forecast" in model_name.lower():
            # Simple forecast fallback: use historical average
            historical_data = input_data.get("historical_sales", [])
            if historical_data:
                avg = sum(historical_data) / len(historical_data)
                return {
                    "forecast": [avg] * 7,  # 7-day forecast with average
                    "confidence": 0.3,
                    "note": "Simplified fallback using historical average"
                }
        
        return None
