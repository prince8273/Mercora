"""Structured logging with JSON format for ELK stack integration."""

import logging
import json
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4


logger = logging.getLogger(__name__)


@dataclass
class LogContext:
    """Context information for structured logging."""
    request_id: str
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    agent_type: Optional[str] = None
    query_id: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted logs for ELK stack.
    
    Features:
    - JSON format for easy parsing by Logstash
    - Automatic context injection (request_id, tenant_id, etc.)
    - Stack trace capture for errors
    - Correlation IDs for distributed tracing
    """
    
    def __init__(self, name: str = __name__):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self.default_context: Dict[str, Any] = {}
    
    def set_default_context(self, context: Dict[str, Any]) -> None:
        """Set default context that will be included in all log messages."""
        self.default_context = context.copy()
    
    def _format_log(
        self,
        level: str,
        message: str,
        context: Optional[LogContext] = None,
        error: Optional[Exception] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Format log message as JSON structure."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "logger": self.logger.name,
        }
        
        # Add default context
        log_entry.update(self.default_context)
        
        # Add specific context
        if context:
            context_dict = asdict(context)
            # Remove None values and empty dicts
            context_dict = {
                k: v for k, v in context_dict.items()
                if v is not None and v != {}
            }
            log_entry.update(context_dict)
        
        # Add error information
        if error:
            log_entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "stack_trace": traceback.format_exc()
            }
        
        # Add additional fields
        log_entry.update(kwargs)
        
        return log_entry
    
    def _log(
        self,
        level: int,
        level_name: str,
        message: str,
        context: Optional[LogContext] = None,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """Internal logging method."""
        log_entry = self._format_log(level_name, message, context, error, **kwargs)
        
        # Log as JSON string
        self.logger.log(level, json.dumps(log_entry))
    
    def debug(
        self,
        message: str,
        context: Optional[LogContext] = None,
        **kwargs
    ) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, "DEBUG", message, context, **kwargs)
    
    def info(
        self,
        message: str,
        context: Optional[LogContext] = None,
        **kwargs
    ) -> None:
        """Log info message."""
        self._log(logging.INFO, "INFO", message, context, **kwargs)
    
    def warning(
        self,
        message: str,
        context: Optional[LogContext] = None,
        **kwargs
    ) -> None:
        """Log warning message."""
        self._log(logging.WARNING, "WARNING", message, context, **kwargs)
    
    def error(
        self,
        message: str,
        context: Optional[LogContext] = None,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """Log error message with optional exception."""
        self._log(logging.ERROR, "ERROR", message, context, error, **kwargs)
    
    def critical(
        self,
        message: str,
        context: Optional[LogContext] = None,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """Log critical message with optional exception."""
        self._log(logging.CRITICAL, "CRITICAL", message, context, error, **kwargs)
    
    def log_agent_execution(
        self,
        agent_type: str,
        execution_time: float,
        status: str,
        context: Optional[LogContext] = None,
        **kwargs
    ) -> None:
        """
        Log agent execution with telemetry.
        
        Validates Property 62: Agent executions are logged with telemetry.
        """
        log_context = context or LogContext(request_id=str(uuid4()))
        log_context.agent_type = agent_type
        
        self.info(
            f"Agent execution completed: {agent_type}",
            context=log_context,
            execution_time_seconds=execution_time,
            status=status,
            **kwargs
        )
    
    def log_error_with_context(
        self,
        message: str,
        error: Exception,
        context: Optional[LogContext] = None,
        **kwargs
    ) -> None:
        """
        Log error with full context and stack trace.
        
        Validates Property 63: Errors are logged with context.
        """
        log_context = context or LogContext(request_id=str(uuid4()))
        
        self.error(
            message,
            context=log_context,
            error=error,
            **kwargs
        )


# Global structured logger instance
_structured_logger: Optional[StructuredLogger] = None


def get_structured_logger(name: str = __name__) -> StructuredLogger:
    """Get or create a structured logger instance."""
    global _structured_logger
    if _structured_logger is None:
        _structured_logger = StructuredLogger(name)
    return _structured_logger


def configure_json_logging() -> None:
    """
    Configure Python logging to output JSON format.
    
    This should be called at application startup to ensure all logs
    are formatted as JSON for ELK stack ingestion.
    """
    # Create JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry["error"] = {
                    "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                    "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                    "stack_trace": self.formatException(record.exc_info) if record.exc_info else None
                }
            
            return json.dumps(log_entry)
    
    # Apply to root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(JSONFormatter())
    
    logger.info("JSON logging configured for ELK stack")
