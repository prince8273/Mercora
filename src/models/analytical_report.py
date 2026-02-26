"""Analytical Report model for storing analysis results"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.product import GUID


class AnalyticalReport(Base):
    """
    Analytical Report model for storing structured analysis results
    
    This model stores the output from multi-agent analysis including:
    - Executive summaries
    - Key metrics and trends
    - Action items and recommendations
    - Risk assessments
    - Data quality warnings
    """
    __tablename__ = "analytical_reports"
    
    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)
    
    # Foreign keys
    tenant_id = Column(GUID(), ForeignKey('tenants.id'), nullable=False, index=True)
    query_id = Column(GUID(), nullable=False, index=True)
    
    # Report content
    executive_summary = Column(Text, nullable=False)
    key_metrics = Column(JSON, nullable=False)  # Dict[str, Any]
    agent_results = Column(JSON, nullable=False)  # List[AgentResult]
    action_items = Column(JSON, nullable=False)  # List[ActionItem]
    risk_assessment = Column(JSON, nullable=True)  # RiskAssessment
    
    # Confidence and quality
    overall_confidence = Column(Float, nullable=False)
    data_quality_warnings = Column(JSON, nullable=True)  # List[str]
    supporting_evidence = Column(JSON, nullable=True)  # List[Evidence]
    
    # Execution metadata
    execution_mode = Column(String(20), nullable=False)  # QUICK or DEEP
    execution_time_ms = Column(Float, nullable=True)
    agents_used = Column(JSON, nullable=True)  # List[str]
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="analytical_reports")
    
    # Indexes
    __table_args__ = (
        Index('idx_analytical_reports_tenant', 'tenant_id'),
        Index('idx_analytical_reports_query', 'query_id'),
        Index('idx_analytical_reports_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AnalyticalReport(id={self.id}, query_id={self.query_id}, tenant_id={self.tenant_id})>"
