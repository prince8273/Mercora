"""Model registry database models"""
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Boolean, ForeignKey, Enum as SQLEnum, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from src.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid.uuid4.__class__):
                return str(value)
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.uuid4.__class__):
                from uuid import UUID
                return UUID(value)
            else:
                return value


class ModelType(str, enum.Enum):
    """Types of ML models"""
    SENTIMENT = "sentiment"
    DEMAND_FORECAST = "demand_forecast"
    PRICE_OPTIMIZATION = "price_optimization"


class ModelStatus(str, enum.Enum):
    """Model deployment status"""
    TRAINING = "training"
    STAGING = "staging"
    ACTIVE = "active"
    ARCHIVED = "archived"
    FAILED = "failed"


class ModelVersion(Base):
    """Model version registry"""
    __tablename__ = "model_versions"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(GUID(), nullable=False, index=True)
    
    # Model identification
    model_type = Column(SQLEnum(ModelType), nullable=False, index=True)
    model_name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    
    # Model metadata
    framework = Column(String(100))  # e.g., "transformers", "prophet", "sklearn"
    algorithm = Column(String(100))  # e.g., "distilbert", "prophet", "random_forest"
    hyperparameters = Column(JSON)
    
    # Storage
    model_path = Column(String(500))  # Path to model file/directory
    model_size_mb = Column(Float)
    
    # Training metadata
    training_data_size = Column(Integer)
    training_duration_seconds = Column(Float)
    trained_at = Column(DateTime, default=datetime.utcnow)
    trained_by = Column(String(255))  # User or system that trained the model
    
    # Performance metrics
    metrics = Column(JSON)  # Store all metrics as JSON
    
    # Status
    status = Column(SQLEnum(ModelStatus), default=ModelStatus.TRAINING, index=True)
    is_active = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived_at = Column(DateTime, nullable=True)
    
    # Relationships
    performance_records = relationship("ModelPerformance", back_populates="model_version", cascade="all, delete-orphan")
    drift_records = relationship("ModelDrift", back_populates="model_version", cascade="all, delete-orphan")


class ModelPerformance(Base):
    """Model performance tracking over time"""
    __tablename__ = "model_performance"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    model_version_id = Column(GUID(), ForeignKey("model_versions.id"), nullable=False, index=True)
    tenant_id = Column(GUID(), nullable=False, index=True)
    
    # Evaluation period
    evaluation_date = Column(DateTime, nullable=False, index=True)
    evaluation_period_start = Column(DateTime)
    evaluation_period_end = Column(DateTime)
    
    # Performance metrics
    metrics = Column(JSON, nullable=False)  # Flexible metrics storage
    
    # Sample size
    predictions_count = Column(Integer)
    actuals_count = Column(Integer)
    
    # Comparison to baseline
    baseline_metrics = Column(JSON)
    improvement_over_baseline = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    model_version = relationship("ModelVersion", back_populates="performance_records")


class ModelDrift(Base):
    """Model drift detection records"""
    __tablename__ = "model_drift"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    model_version_id = Column(GUID(), ForeignKey("model_versions.id"), nullable=False, index=True)
    tenant_id = Column(GUID(), nullable=False, index=True)
    
    # Drift detection
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    drift_type = Column(String(50))  # "performance", "data", "concept"
    
    # Drift metrics
    metric_name = Column(String(100))  # e.g., "f1_score", "mape"
    baseline_value = Column(Float)
    current_value = Column(Float)
    drift_percentage = Column(Float)
    
    # Severity
    is_significant = Column(Boolean, default=False)
    severity = Column(String(20))  # "low", "medium", "high", "critical"
    
    # Alert status
    alert_sent = Column(Boolean, default=False)
    alert_sent_at = Column(DateTime, nullable=True)
    
    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(String(1000))
    
    # Additional data
    drift_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    model_version = relationship("ModelVersion", back_populates="drift_records")


class RetrainingJob(Base):
    """Model retraining job tracking"""
    __tablename__ = "retraining_jobs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(GUID(), nullable=False, index=True)
    
    # Job identification
    model_type = Column(SQLEnum(ModelType), nullable=False, index=True)
    trigger_reason = Column(String(255))  # "drift_detected", "scheduled", "manual"
    
    # Source model
    source_model_version_id = Column(GUID(), ForeignKey("model_versions.id"), nullable=True)
    
    # Job status
    status = Column(String(50), default="queued", index=True)  # queued, running, completed, failed
    
    # Training configuration
    training_config = Column(JSON)
    training_data_size = Column(Integer)
    
    # Execution
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float)
    
    # Results
    new_model_version_id = Column(GUID(), ForeignKey("model_versions.id"), nullable=True)
    metrics = Column(JSON)
    error_message = Column(String(1000))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
