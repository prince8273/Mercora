"""Model registry service for managing ML model versions"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.models.model_registry import (
    ModelVersion,
    ModelPerformance,
    ModelDrift,
    RetrainingJob,
    ModelType,
    ModelStatus
)

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Central registry for ML model management.
    
    Responsibilities:
    - Model versioning and metadata storage
    - Performance tracking over time
    - Drift detection and alerting
    - Retraining workflow coordination
    - A/B testing support
    """
    
    def __init__(self, db: Session, tenant_id: UUID):
        """
        Initialize model registry.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
        """
        self.db = db
        self.tenant_id = tenant_id
    
    def register_model(
        self,
        model_type: ModelType,
        model_name: str,
        version: str,
        framework: str,
        algorithm: str,
        model_path: str,
        metrics: Dict[str, float],
        hyperparameters: Optional[Dict[str, Any]] = None,
        training_data_size: Optional[int] = None,
        training_duration_seconds: Optional[float] = None,
        model_size_mb: Optional[float] = None
    ) -> ModelVersion:
        """
        Register a new model version.
        
        Args:
            model_type: Type of model (sentiment, demand_forecast, etc.)
            model_name: Name of the model
            version: Version string (e.g., "1.0.0", "2023-02-20-001")
            framework: ML framework used (e.g., "transformers", "prophet")
            algorithm: Algorithm name (e.g., "distilbert", "prophet")
            model_path: Path to model files
            metrics: Performance metrics dictionary
            hyperparameters: Model hyperparameters
            training_data_size: Number of training samples
            training_duration_seconds: Training time
            model_size_mb: Model size in MB
            
        Returns:
            ModelVersion object
        """
        model_version = ModelVersion(
            tenant_id=self.tenant_id,
            model_type=model_type,
            model_name=model_name,
            version=version,
            framework=framework,
            algorithm=algorithm,
            model_path=model_path,
            metrics=metrics,
            hyperparameters=hyperparameters or {},
            training_data_size=training_data_size,
            training_duration_seconds=training_duration_seconds,
            model_size_mb=model_size_mb,
            status=ModelStatus.STAGING,
            trained_at=datetime.utcnow()
        )
        
        self.db.add(model_version)
        self.db.commit()
        self.db.refresh(model_version)
        
        logger.info(
            f"Registered model {model_name} v{version} "
            f"(type={model_type}, id={model_version.id})"
        )
        
        return model_version
    
    def get_active_model(self, model_type: ModelType) -> Optional[ModelVersion]:
        """
        Get the currently active model for a given type.
        
        Args:
            model_type: Type of model
            
        Returns:
            Active ModelVersion or None
        """
        return self.db.query(ModelVersion).filter(
            ModelVersion.tenant_id == self.tenant_id,
            ModelVersion.model_type == model_type,
            ModelVersion.is_active == True,
            ModelVersion.status == ModelStatus.ACTIVE
        ).first()
    
    def promote_model(self, model_version_id: UUID) -> ModelVersion:
        """
        Promote a model version to active status.
        
        Demotes any currently active model of the same type.
        
        Args:
            model_version_id: Model version ID to promote
            
        Returns:
            Promoted ModelVersion
        """
        # Get the model to promote
        model = self.db.query(ModelVersion).filter(
            ModelVersion.id == model_version_id,
            ModelVersion.tenant_id == self.tenant_id
        ).first()
        
        if not model:
            raise ValueError(f"Model version {model_version_id} not found")
        
        # Demote any currently active models of the same type
        self.db.query(ModelVersion).filter(
            ModelVersion.tenant_id == self.tenant_id,
            ModelVersion.model_type == model.model_type,
            ModelVersion.is_active == True
        ).update({
            "is_active": False,
            "status": ModelStatus.ARCHIVED,
            "archived_at": datetime.utcnow()
        })
        
        # Promote the new model
        model.is_active = True
        model.status = ModelStatus.ACTIVE
        model.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(model)
        
        logger.info(
            f"Promoted model {model.model_name} v{model.version} "
            f"to active (type={model.model_type})"
        )
        
        return model
    
    def record_model_performance(
        self,
        model_version_id: UUID,
        metrics: Dict[str, float],
        evaluation_date: datetime,
        predictions_count: int,
        actuals_count: int,
        evaluation_period_start: Optional[datetime] = None,
        evaluation_period_end: Optional[datetime] = None,
        baseline_metrics: Optional[Dict[str, float]] = None
    ) -> ModelPerformance:
        """
        Record model performance for a specific evaluation period.
        
        Args:
            model_version_id: Model version ID
            metrics: Performance metrics dictionary
            evaluation_date: Date of evaluation
            predictions_count: Number of predictions made
            actuals_count: Number of actuals available
            evaluation_period_start: Start of evaluation period
            evaluation_period_end: End of evaluation period
            baseline_metrics: Baseline metrics for comparison
            
        Returns:
            ModelPerformance record
        """
        # Calculate improvement over baseline if provided
        improvement = None
        if baseline_metrics and metrics:
            # Use first metric for improvement calculation
            metric_name = list(metrics.keys())[0]
            if metric_name in baseline_metrics:
                baseline_val = baseline_metrics[metric_name]
                current_val = metrics[metric_name]
                if baseline_val != 0:
                    improvement = ((current_val - baseline_val) / abs(baseline_val)) * 100
        
        performance = ModelPerformance(
            model_version_id=model_version_id,
            tenant_id=self.tenant_id,
            evaluation_date=evaluation_date,
            evaluation_period_start=evaluation_period_start,
            evaluation_period_end=evaluation_period_end,
            metrics=metrics,
            predictions_count=predictions_count,
            actuals_count=actuals_count,
            baseline_metrics=baseline_metrics,
            improvement_over_baseline=improvement
        )
        
        self.db.add(performance)
        self.db.commit()
        self.db.refresh(performance)
        
        logger.info(
            f"Recorded performance for model {model_version_id}: "
            f"metrics={metrics}, improvement={improvement}"
        )
        
        return performance
    
    def detect_drift(
        self,
        model_version_id: UUID,
        metric_name: str,
        current_value: float,
        baseline_value: float,
        threshold_percentage: float = 10.0
    ) -> Optional[ModelDrift]:
        """
        Detect and record model drift.
        
        Args:
            model_version_id: Model version ID
            metric_name: Name of the metric (e.g., "f1_score", "mape")
            current_value: Current metric value
            baseline_value: Baseline metric value
            threshold_percentage: Drift threshold percentage
            
        Returns:
            ModelDrift record if drift detected, None otherwise
        """
        # Calculate drift percentage
        if baseline_value == 0:
            drift_pct = 0.0
        else:
            drift_pct = ((baseline_value - current_value) / abs(baseline_value)) * 100
        
        # Check if drift is significant
        is_significant = abs(drift_pct) >= threshold_percentage
        
        if not is_significant:
            return None
        
        # Determine severity
        abs_drift = abs(drift_pct)
        if abs_drift >= 30:
            severity = "critical"
        elif abs_drift >= 20:
            severity = "high"
        elif abs_drift >= 15:
            severity = "medium"
        else:
            severity = "low"
        
        # Record drift
        drift = ModelDrift(
            model_version_id=model_version_id,
            tenant_id=self.tenant_id,
            drift_type="performance",
            metric_name=metric_name,
            baseline_value=baseline_value,
            current_value=current_value,
            drift_percentage=drift_pct,
            is_significant=is_significant,
            severity=severity
        )
        
        self.db.add(drift)
        self.db.commit()
        self.db.refresh(drift)
        
        logger.warning(
            f"Drift detected for model {model_version_id}: "
            f"{metric_name} changed from {baseline_value:.4f} to {current_value:.4f} "
            f"({drift_pct:+.2f}%, severity={severity})"
        )
        
        return drift
    
    def check_retraining_needed(
        self,
        model_type: ModelType,
        sentiment_f1_threshold: float = 0.85,
        forecast_mape_threshold: float = 20.0
    ) -> bool:
        """
        Check if model retraining is needed based on performance thresholds.
        
        Args:
            model_type: Type of model to check
            sentiment_f1_threshold: F1 score threshold for sentiment models
            forecast_mape_threshold: MAPE threshold for forecast models
            
        Returns:
            True if retraining is needed
        """
        active_model = self.get_active_model(model_type)
        if not active_model:
            return False
        
        # Get latest performance record
        latest_perf = self.db.query(ModelPerformance).filter(
            ModelPerformance.model_version_id == active_model.id,
            ModelPerformance.tenant_id == self.tenant_id
        ).order_by(desc(ModelPerformance.evaluation_date)).first()
        
        if not latest_perf:
            return False
        
        # Check thresholds based on model type
        if model_type == ModelType.SENTIMENT:
            f1_score = latest_perf.metrics.get('f1_score', 1.0)
            return f1_score < sentiment_f1_threshold
        
        elif model_type == ModelType.DEMAND_FORECAST:
            mape = latest_perf.metrics.get('mape', 0.0)
            return mape > forecast_mape_threshold
        
        return False
    
    def trigger_retraining(
        self,
        model_type: ModelType,
        trigger_reason: str,
        training_config: Optional[Dict[str, Any]] = None
    ) -> RetrainingJob:
        """
        Trigger a model retraining job.
        
        Args:
            model_type: Type of model to retrain
            trigger_reason: Reason for retraining (e.g., "drift_detected", "scheduled")
            training_config: Training configuration
            
        Returns:
            RetrainingJob record
        """
        # Get current active model
        active_model = self.get_active_model(model_type)
        
        job = RetrainingJob(
            tenant_id=self.tenant_id,
            model_type=model_type,
            trigger_reason=trigger_reason,
            source_model_version_id=active_model.id if active_model else None,
            training_config=training_config or {},
            status="queued"
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        logger.info(
            f"Triggered retraining job for {model_type} "
            f"(reason={trigger_reason}, job_id={job.id})"
        )
        
        return job
    
    def get_model_versions(
        self,
        model_type: Optional[ModelType] = None,
        limit: int = 10
    ) -> List[ModelVersion]:
        """
        Get model versions, optionally filtered by type.
        
        Args:
            model_type: Optional model type filter
            limit: Maximum number of versions to return
            
        Returns:
            List of ModelVersion objects
        """
        query = self.db.query(ModelVersion).filter(
            ModelVersion.tenant_id == self.tenant_id
        )
        
        if model_type:
            query = query.filter(ModelVersion.model_type == model_type)
        
        return query.order_by(desc(ModelVersion.created_at)).limit(limit).all()
    
    def get_performance_history(
        self,
        model_version_id: UUID,
        days: int = 30
    ) -> List[ModelPerformance]:
        """
        Get performance history for a model version.
        
        Args:
            model_version_id: Model version ID
            days: Number of days of history to retrieve
            
        Returns:
            List of ModelPerformance records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return self.db.query(ModelPerformance).filter(
            ModelPerformance.model_version_id == model_version_id,
            ModelPerformance.tenant_id == self.tenant_id,
            ModelPerformance.evaluation_date >= cutoff_date
        ).order_by(ModelPerformance.evaluation_date).all()
    
    def get_drift_alerts(
        self,
        model_type: Optional[ModelType] = None,
        unresolved_only: bool = True
    ) -> List[ModelDrift]:
        """
        Get drift alerts, optionally filtered by model type.
        
        Args:
            model_type: Optional model type filter
            unresolved_only: Only return unresolved alerts
            
        Returns:
            List of ModelDrift records
        """
        query = self.db.query(ModelDrift).join(ModelVersion).filter(
            ModelDrift.tenant_id == self.tenant_id,
            ModelDrift.is_significant == True
        )
        
        if model_type:
            query = query.filter(ModelVersion.model_type == model_type)
        
        if unresolved_only:
            query = query.filter(ModelDrift.resolved == False)
        
        return query.order_by(desc(ModelDrift.detected_at)).all()
    
    def get_retraining_jobs(
        self,
        model_type: Optional[ModelType] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[RetrainingJob]:
        """
        Get retraining jobs, optionally filtered.
        
        Args:
            model_type: Optional model type filter
            status: Optional status filter
            limit: Maximum number of jobs to return
            
        Returns:
            List of RetrainingJob records
        """
        query = self.db.query(RetrainingJob).filter(
            RetrainingJob.tenant_id == self.tenant_id
        )
        
        if model_type:
            query = query.filter(RetrainingJob.model_type == model_type)
        
        if status:
            query = query.filter(RetrainingJob.status == status)
        
        return query.order_by(desc(RetrainingJob.created_at)).limit(limit).all()
