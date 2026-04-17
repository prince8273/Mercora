"""Query history model"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Numeric, DateTime, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.product import GUID


class QueryHistory(Base):
    """Persisted query history per tenant/user"""
    __tablename__ = "query_history"

    id = Column(GUID(), primary_key=True, default=uuid4)
    tenant_id = Column(GUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)

    # Query details
    query_text = Column(String, nullable=False)
    execution_mode = Column(String(20), nullable=False)   # quick / deep
    agents_executed = Column(JSON, nullable=False, default=list)

    # Result summary
    overall_confidence = Column(Numeric(6, 2), nullable=True)  # 0.00 - 100.00
    execution_time_seconds = Column(Numeric(8, 2), nullable=True)
    status = Column(String(20), nullable=False, default="success")  # success / failure
    error_message = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="query_history")
    user = relationship("User", back_populates="query_history")

    __table_args__ = (
        Index("idx_query_history_tenant_created", "tenant_id", "created_at"),
        Index("idx_query_history_user", "user_id"),
    )

    def __repr__(self):
        return f"<QueryHistory(id={self.id}, tenant={self.tenant_id}, query={self.query_text[:40]!r})>"
