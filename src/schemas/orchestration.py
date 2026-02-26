"""Orchestration schemas for query routing and execution"""
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ExecutionMode(str, Enum):
    """Execution mode for query processing"""
    QUICK = "quick"  # 2 minute target, uses cached data
    DEEP = "deep"    # 10 minute target, full analysis


class AgentType(str, Enum):
    """Types of intelligence agents"""
    PRICING = "pricing"
    SENTIMENT = "sentiment"
    DEMAND_FORECAST = "demand_forecast"
    DATA_QA = "data_qa"


class Priority(str, Enum):
    """Request priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class QueryPattern(BaseModel):
    """Matched query pattern"""
    pattern_name: str
    confidence: float = Field(..., ge=0, le=1)
    matched_keywords: List[str]
    suggested_agents: List[AgentType]
    
    model_config = ConfigDict(from_attributes=True)


class ConversationContext(BaseModel):
    """Context from previous conversation turns"""
    conversation_id: UUID
    previous_queries: List[str] = Field(default_factory=list)
    previous_results: List[Dict[str, Any]] = Field(default_factory=list)
    user_preferences: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class RoutingDecision(BaseModel):
    """Decision on how to route a query"""
    execution_mode: ExecutionMode
    required_agents: List[AgentType]
    use_cache: bool
    cache_key: Optional[str] = None
    estimated_duration: Optional[timedelta] = None
    
    model_config = ConfigDict(from_attributes=True)


class ParsedQuery(BaseModel):
    """Parsed and understood query"""
    original_query: str
    intent: str
    entities: Dict[str, Any] = Field(default_factory=dict)
    required_agents: List[AgentType]
    execution_mode: ExecutionMode
    filters: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class QueryUnderstanding(BaseModel):
    """LLM's understanding of the query"""
    intent: str
    key_entities: Dict[str, Any]
    required_capabilities: List[str]
    suggested_agents: List[AgentType]
    reasoning: str
    confidence: float = Field(..., ge=0, le=1)
    
    model_config = ConfigDict(from_attributes=True)


class AgentTask(BaseModel):
    """Task for a specific agent"""
    agent_type: AgentType
    parameters: Dict[str, Any]
    dependencies: List[AgentType] = Field(default_factory=list)
    timeout_seconds: int = 120
    
    model_config = ConfigDict(from_attributes=True)


class ExecutionPlan(BaseModel):
    """Plan for executing multiple agents"""
    tasks: List[AgentTask]
    execution_mode: ExecutionMode
    parallel_groups: List[List[AgentType]] = Field(default_factory=list)
    estimated_duration: timedelta
    
    model_config = ConfigDict(from_attributes=True)


class AgentResult(BaseModel):
    """Result from an agent execution"""
    agent_type: AgentType
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float
    confidence: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class CachedResult(BaseModel):
    """Cached query result"""
    query_hash: str
    result: Dict[str, Any]
    cached_at: datetime
    expires_at: datetime
    hit_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class QueuePosition(BaseModel):
    """Position in execution queue"""
    position: int
    estimated_wait_time: timedelta
    request_id: UUID
    
    model_config = ConfigDict(from_attributes=True)


class QueryRequest(BaseModel):
    """Query request for execution"""
    request_id: UUID
    query: str
    tenant_id: UUID
    user_id: UUID
    execution_mode: ExecutionMode
    priority: Priority = Priority.NORMAL
    context: Optional[ConversationContext] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(from_attributes=True)


class TokenUsage(BaseModel):
    """LLM token usage tracking"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    cost_usd: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class FallbackStrategy(str, Enum):
    """Strategy for handling agent failures"""
    SKIP = "skip"  # Skip failed agent, continue with others
    RETRY = "retry"  # Retry the agent
    FAIL = "fail"  # Fail entire request
    USE_CACHE = "use_cache"  # Use cached result if available
