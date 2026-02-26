"""
Data models for Domain Memory

Defines data structures for user preferences, conversation context,
and business context storage.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID


@dataclass
class KPI:
    """Key Performance Indicator preference"""
    name: str
    enabled: bool
    priority: int = 1
    threshold: Optional[float] = None


@dataclass
class UserPreferences:
    """User preferences for personalization"""
    user_id: UUID
    tenant_id: UUID
    kpi_preferences: Dict[str, bool] = field(default_factory=dict)
    marketplace_focus: List[str] = field(default_factory=list)
    business_goals: Dict[str, Any] = field(default_factory=dict)
    notification_settings: Dict[str, bool] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": str(self.user_id),
            "tenant_id": str(self.tenant_id),
            "kpi_preferences": self.kpi_preferences,
            "marketplace_focus": self.marketplace_focus,
            "business_goals": self.business_goals,
            "notification_settings": self.notification_settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class ConversationContext:
    """Conversation context for follow-up queries"""
    conversation_id: UUID
    tenant_id: UUID
    user_id: UUID
    messages: List[Dict[str, Any]] = field(default_factory=list)
    last_query: Optional[str] = None
    last_result: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "conversation_id": str(self.conversation_id),
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id),
            "messages": self.messages,
            "last_query": self.last_query,
            "last_result": self.last_result,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class BusinessContext:
    """Business context for tenant"""
    tenant_id: UUID
    industry: Optional[str] = None
    target_markets: List[str] = field(default_factory=list)
    business_goals: List[str] = field(default_factory=list)
    kpis: List[KPI] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tenant_id": str(self.tenant_id),
            "industry": self.industry,
            "target_markets": self.target_markets,
            "business_goals": self.business_goals,
            "kpis": [{"name": kpi.name, "enabled": kpi.enabled, "priority": kpi.priority} for kpi in self.kpis],
            "constraints": self.constraints,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class HistoricalQuery:
    """Historical query with result"""
    query_id: UUID
    tenant_id: UUID
    user_id: UUID
    query_text: str
    result_summary: str
    confidence: float
    execution_time_ms: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    similarity_score: Optional[float] = None  # For semantic search results
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query_id": str(self.query_id),
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id),
            "query_text": self.query_text,
            "result_summary": self.result_summary,
            "confidence": self.confidence,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "similarity_score": self.similarity_score
        }
