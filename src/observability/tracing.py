"""Distributed tracing with Jaeger integration."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4
from contextvars import ContextVar

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import Resource
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    # Fallback stubs
    class TracerProvider:
        def __init__(self, *args, **kwargs): pass
        def get_tracer(self, *args, **kwargs): return None
    
    class BatchSpanProcessor:
        def __init__(self, *args, **kwargs): pass
    
    class JaegerExporter:
        def __init__(self, *args, **kwargs): pass
    
    class Resource:
        @staticmethod
        def create(*args, **kwargs): return None


logger = logging.getLogger(__name__)


# Context variable for current trace
_current_trace_context: ContextVar[Optional['TraceContext']] = ContextVar(
    'trace_context',
    default=None
)


@dataclass
class TraceContext:
    """Context for distributed tracing."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    tags: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace context to dictionary."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "tags": self.tags,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


@dataclass
class Span:
    """Represents a span in distributed tracing."""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def finish(self) -> None:
        """Mark span as finished."""
        self.end_time = datetime.utcnow()
    
    def add_tag(self, key: str, value: Any) -> None:
        """Add a tag to the span."""
        self.tags[key] = value
    
    def log_event(self, event: str, **kwargs) -> None:
        """Log an event in the span."""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            **kwargs
        })


class TracingManager:
    """
    Distributed tracing manager with Jaeger integration.
    
    Features:
    - Create and manage distributed traces
    - Propagate trace context across components
    - Export traces to Jaeger for visualization
    - Support for nested spans
    """
    
    def __init__(
        self,
        service_name: str = "ecommerce-intelligence-agent",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831,
        enabled: bool = True
    ):
        """Initialize tracing manager."""
        self.service_name = service_name
        self.enabled = enabled and OPENTELEMETRY_AVAILABLE
        self.spans: Dict[str, Span] = {}
        
        if not OPENTELEMETRY_AVAILABLE:
            logger.warning(
                "OpenTelemetry not installed. Distributed tracing disabled. "
                "Install with: pip install opentelemetry-api opentelemetry-sdk "
                "opentelemetry-exporter-jaeger"
            )
            return
        
        if self.enabled:
            try:
                # Create Jaeger exporter
                jaeger_exporter = JaegerExporter(
                    agent_host_name=jaeger_host,
                    agent_port=jaeger_port,
                )
                
                # Create tracer provider
                resource = Resource.create({"service.name": service_name})
                provider = TracerProvider(resource=resource)
                processor = BatchSpanProcessor(jaeger_exporter)
                provider.add_span_processor(processor)
                
                # Set as global tracer provider
                trace.set_tracer_provider(provider)
                self.tracer = provider.get_tracer(__name__)
                
                logger.info(
                    f"Tracing initialized: {service_name} -> "
                    f"{jaeger_host}:{jaeger_port}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize tracing: {e}")
                self.enabled = False
    
    def start_trace(
        self,
        operation_name: str,
        tags: Optional[Dict[str, Any]] = None
    ) -> TraceContext:
        """
        Start a new distributed trace.
        
        Validates Property 64: Requests are traced end-to-end.
        """
        trace_id = str(uuid4())
        span_id = str(uuid4())
        
        context = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            operation_name=operation_name,
            tags=tags or {}
        )
        
        # Create span
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=None,
            operation_name=operation_name,
            start_time=datetime.utcnow(),
            tags=tags or {}
        )
        
        self.spans[span_id] = span
        _current_trace_context.set(context)
        
        logger.debug(f"Started trace: {trace_id} ({operation_name})")
        return context
    
    def start_span(
        self,
        operation_name: str,
        parent_context: Optional[TraceContext] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> TraceContext:
        """Start a new span within a trace."""
        # Get parent context from argument or context var
        parent = parent_context or _current_trace_context.get()
        
        if parent is None:
            # No parent, start new trace
            return self.start_trace(operation_name, tags)
        
        span_id = str(uuid4())
        
        context = TraceContext(
            trace_id=parent.trace_id,
            span_id=span_id,
            parent_span_id=parent.span_id,
            operation_name=operation_name,
            tags=tags or {}
        )
        
        # Create span
        span = Span(
            span_id=span_id,
            trace_id=parent.trace_id,
            parent_span_id=parent.span_id,
            operation_name=operation_name,
            start_time=datetime.utcnow(),
            tags=tags or {}
        )
        
        self.spans[span_id] = span
        
        logger.debug(
            f"Started span: {span_id} in trace {parent.trace_id} ({operation_name})"
        )
        return context
    
    def finish_span(self, context: TraceContext) -> None:
        """Finish a span."""
        span = self.spans.get(context.span_id)
        if span:
            span.finish()
            context.end_time = span.end_time
            logger.debug(f"Finished span: {context.span_id}")
    
    def add_span_tag(self, context: TraceContext, key: str, value: Any) -> None:
        """Add a tag to a span."""
        span = self.spans.get(context.span_id)
        if span:
            span.add_tag(key, value)
            context.tags[key] = value
    
    def log_span_event(self, context: TraceContext, event: str, **kwargs) -> None:
        """Log an event in a span."""
        span = self.spans.get(context.span_id)
        if span:
            span.log_event(event, **kwargs)
    
    def get_trace_context(self) -> Optional[TraceContext]:
        """Get the current trace context."""
        return _current_trace_context.get()
    
    def set_trace_context(self, context: Optional[TraceContext]) -> None:
        """Set the current trace context."""
        _current_trace_context.set(context)
    
    def get_span(self, span_id: str) -> Optional[Span]:
        """Get a span by ID."""
        return self.spans.get(span_id)
    
    def get_trace_spans(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace."""
        return [
            span for span in self.spans.values()
            if span.trace_id == trace_id
        ]


# Global tracing manager instance
_tracing_manager: Optional[TracingManager] = None


def get_tracing_manager() -> TracingManager:
    """Get or create the global tracing manager instance."""
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager()
    return _tracing_manager


class trace_span:
    """Context manager for tracing a code block."""
    
    def __init__(
        self,
        operation_name: str,
        tags: Optional[Dict[str, Any]] = None,
        manager: Optional[TracingManager] = None
    ):
        self.operation_name = operation_name
        self.tags = tags
        self.manager = manager or get_tracing_manager()
        self.context: Optional[TraceContext] = None
    
    def __enter__(self) -> TraceContext:
        """Start span on enter."""
        self.context = self.manager.start_span(self.operation_name, tags=self.tags)
        return self.context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finish span on exit."""
        if self.context:
            if exc_type:
                self.manager.add_span_tag(self.context, "error", True)
                self.manager.add_span_tag(self.context, "error.type", exc_type.__name__)
                self.manager.add_span_tag(self.context, "error.message", str(exc_val))
            self.manager.finish_span(self.context)
