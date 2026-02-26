"""Enhanced structured report schemas"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class TrendDirection(str, Enum):
    """Trend direction for metrics"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    UNKNOWN = "unknown"


class SeverityLevel(str, Enum):
    """Severity level for risks"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class MetricWithTrend(BaseModel):
    """Metric with current value and trend"""
    name: str
    value: Any
    unit: Optional[str] = None
    trend: TrendDirection
    change_percentage: Optional[float] = None
    previous_value: Optional[Any] = None
    confidence: float = Field(..., ge=0, le=1)
    
    model_config = ConfigDict(from_attributes=True)


class RiskAssessment(BaseModel):
    """Risk assessment with severity"""
    risk_id: str
    title: str
    description: str
    severity: SeverityLevel
    impact: str
    likelihood: str
    mitigation: Optional[str] = None
    affected_areas: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1)
    
    model_config = ConfigDict(from_attributes=True)


class DataQualityWarning(BaseModel):
    """Data quality warning"""
    warning_id: str
    message: str
    severity: SeverityLevel
    affected_data: str
    recommendation: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SupportingEvidence(BaseModel):
    """Supporting evidence with data lineage"""
    evidence_id: str
    insight_id: str
    source_data_type: str
    source_record_ids: List[str] = Field(default_factory=list)
    data_lineage_path: List[str] = Field(default_factory=list)
    transformation_applied: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(from_attributes=True)


class Insight(BaseModel):
    """Insight with traceability"""
    insight_id: str
    title: str
    description: str
    category: str
    agent_source: str
    confidence: float = Field(..., ge=0, le=1)
    supporting_evidence: List[SupportingEvidence] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class ActionItem(BaseModel):
    """Prioritized action item"""
    action_id: str
    title: str
    description: str
    priority: str  # high, medium, low
    impact: str  # high, medium, low
    urgency: str  # high, medium, low
    source_agent: str
    confidence: float = Field(..., ge=0, le=1)
    estimated_effort: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class UncertaintyCommunication(BaseModel):
    """Explicit uncertainty communication"""
    aspect: str
    uncertainty_level: str  # high, medium, low
    reason: str
    data_limitations: List[str] = Field(default_factory=list)
    confidence_interval: Optional[Dict[str, float]] = None
    
    model_config = ConfigDict(from_attributes=True)


class StructuredReport(BaseModel):
    """Enhanced structured report with full traceability"""
    report_id: UUID
    tenant_id: UUID
    query: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Executive summary (Requirement 7.1)
    executive_summary: str
    
    # Metrics with trends (Requirement 7.2)
    key_metrics: List[MetricWithTrend] = Field(default_factory=list)
    
    # Insights with traceability (Requirement 7.3)
    insights: List[Insight] = Field(default_factory=list)
    
    # Risk assessment (Requirement 7.4)
    risks: List[RiskAssessment] = Field(default_factory=list)
    
    # Recommendations with confidence (Requirement 7.5)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Prioritized action items (Requirement 7.6)
    action_items: List[ActionItem] = Field(default_factory=list)
    
    # Uncertainty communication (Requirement 7.7)
    uncertainties: List[UncertaintyCommunication] = Field(default_factory=list)
    
    # Data quality warnings
    data_quality_warnings: List[DataQualityWarning] = Field(default_factory=list)
    
    # Overall confidence score (0-100 scale)
    overall_confidence: float = Field(..., ge=0, le=100)
    
    # Agent execution summary
    agent_results: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)
