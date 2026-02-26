"""
Automated Retraining Workflow - Triggers and manages model retraining

This module handles automated model retraining when performance
falls below thresholds or drift is detected.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RetrainingStatus(str, Enum):
    """Status of retraining workflow"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RetrainingJob:
    """Represents a model retraining job"""
    id: UUID
    model_name: str
    current_version: str
    trigger_reason: str  # drift, threshold_breach, manual
    trigger_metrics: Dict[str, float]
    status: RetrainingStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    new_version: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RetrainingWorkflow:
    """
    Manages automated model retraining workflow.
    
    Triggers retraining when performance falls below thresholds,
    manages retraining jobs, and handles model versioning.
    """
    
    def __init__(self, model_registry, model_monitor):
        """
        Initialize retraining workflow.
        
        Args:
            model_registry: ModelRegistry instance
            model_monitor: ModelPerformanceMonitor instance
        """
        self.model_registry = model_registry
        self.model_monitor = model_monitor
        self._retraining_jobs: Dict[UUID, RetrainingJob] = {}
        self._retraining_callbacks: Dict[str, Callable] = {}  # model_name -> callback
        logger.info("RetrainingWorkflow initialized")
    
    def register_retraining_callback(
        self,
        model_name: str,
        callback: Callable[[str, str], str]
    ) -> None:
        """
        Register a callback function for model retraining.
        
        The callback should accept (model_name, current_version) and
        return the new version string after retraining.
        
        Args:
            model_name: Name of the model
            callback: Function to call for retraining
        """
        self._retraining_callbacks[model_name] = callback
        logger.info(f"Registered retraining callback for {model_name}")
    
    def trigger_retraining(
        self,
        model_name: str,
        current_version: str,
        reason: str,
        metrics: Dict[str, float]
    ) -> UUID:
        """
        Trigger a retraining job for a model.
        
        Args:
            model_name: Name of the model
            current_version: Current version of the model
            reason: Reason for retraining (drift, threshold_breach, manual)
            metrics: Performance metrics that triggered retraining
            
        Returns:
            UUID of the retraining job
        """
        job = RetrainingJob(
            id=uuid4(),
            model_name=model_name,
            current_version=current_version,
            trigger_reason=reason,
            trigger_metrics=metrics,
            status=RetrainingStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        self._retraining_jobs[job.id] = job
        logger.info(f"Triggered retraining for {model_name} v{current_version}: {reason}")
        
        # Execute retraining if callback is registered
        if model_name in self._retraining_callbacks:
            self._execute_retraining(job.id)
        else:
            logger.warning(f"No retraining callback registered for {model_name}")
        
        return job.id
    
    def _execute_retraining(self, job_id: UUID) -> None:
        """
        Execute a retraining job.
        
        Args:
            job_id: UUID of the retraining job
        """
        job = self._retraining_jobs.get(job_id)
        if not job:
            logger.error(f"Retraining job {job_id} not found")
            return
        
        job.status = RetrainingStatus.IN_PROGRESS
        job.started_at = datetime.utcnow()
        
        try:
            # Call retraining callback
            callback = self._retraining_callbacks[job.model_name]
            new_version = callback(job.model_name, job.current_version)
            
            # Register new model version
            self.model_registry.register_model(
                model_name=job.model_name,
                model_version=new_version,
                model_artifact_path=f"/models/{job.model_name}/{new_version}",
                metadata={
                    "retrained_from": job.current_version,
                    "trigger_reason": job.trigger_reason,
                    "trigger_metrics": job.trigger_metrics
                }
            )
            
            # Update job status
            job.status = RetrainingStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.new_version = new_version
            
            logger.info(f"Retraining completed: {job.model_name} v{new_version}")
        
        except Exception as e:
            job.status = RetrainingStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            logger.error(f"Retraining failed for {job.model_name}: {e}")
    
    def check_and_trigger_retraining(
        self,
        model_name: str,
        model_version: str,
        metrics: Dict[str, float]
    ) -> Optional[UUID]:
        """
        Check if retraining should be triggered based on metrics.
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            metrics: Current performance metrics
            
        Returns:
            UUID of retraining job if triggered, None otherwise
        """
        # Check for threshold breaches
        threshold_alerts = self.model_monitor.check_performance_thresholds(
            model_name=model_name,
            model_version=model_version,
            metrics=metrics
        )
        
        if threshold_alerts:
            # Trigger retraining due to threshold breach
            return self.trigger_retraining(
                model_name=model_name,
                current_version=model_version,
                reason="threshold_breach",
                metrics=metrics
            )
        
        # Check for drift
        drift_alerts = self.model_monitor.detect_drift(
            model_name=model_name,
            model_version=model_version,
            current_metrics=metrics
        )
        
        if drift_alerts:
            # Trigger retraining due to drift
            return self.trigger_retraining(
                model_name=model_name,
                current_version=model_version,
                reason="drift",
                metrics=metrics
            )
        
        return None
    
    def get_retraining_job(self, job_id: UUID) -> Optional[RetrainingJob]:
        """
        Get a retraining job by ID.
        
        Args:
            job_id: UUID of the retraining job
            
        Returns:
            RetrainingJob or None if not found
        """
        return self._retraining_jobs.get(job_id)
    
    def list_retraining_jobs(
        self,
        model_name: Optional[str] = None,
        status: Optional[RetrainingStatus] = None,
        limit: int = 100
    ) -> list[RetrainingJob]:
        """
        List retraining jobs.
        
        Args:
            model_name: Optional filter by model name
            status: Optional filter by status
            limit: Maximum number of jobs to return
            
        Returns:
            List of RetrainingJob objects, sorted by creation date (newest first)
        """
        jobs = [
            job for job in self._retraining_jobs.values()
            if (model_name is None or job.model_name == model_name)
            and (status is None or job.status == status)
        ]
        
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]
    
    def cancel_retraining_job(self, job_id: UUID) -> bool:
        """
        Cancel a pending retraining job.
        
        Args:
            job_id: UUID of the retraining job
            
        Returns:
            True if cancelled, False if not found or already in progress
        """
        job = self._retraining_jobs.get(job_id)
        if not job:
            logger.warning(f"Retraining job {job_id} not found")
            return False
        
        if job.status != RetrainingStatus.PENDING:
            logger.warning(f"Cannot cancel job {job_id} with status {job.status}")
            return False
        
        job.status = RetrainingStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        logger.info(f"Cancelled retraining job {job_id}")
        return True
    
    def setup_ab_testing(
        self,
        model_name: str,
        version_a: str,
        version_b: str,
        traffic_split: float = 0.5
    ) -> Dict[str, Any]:
        """
        Set up A/B testing for two model versions.
        
        Args:
            model_name: Name of the model
            version_a: First version to test
            version_b: Second version to test
            traffic_split: Fraction of traffic for version_a (0.0-1.0)
            
        Returns:
            A/B test configuration
        """
        # Verify both versions exist
        model_a = self.model_registry.get_model_by_version(model_name, version_a)
        model_b = self.model_registry.get_model_by_version(model_name, version_b)
        
        if not model_a or not model_b:
            raise ValueError(f"One or both versions not found: {version_a}, {version_b}")
        
        ab_config = {
            "model_name": model_name,
            "version_a": version_a,
            "version_b": version_b,
            "traffic_split": traffic_split,
            "started_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        logger.info(f"Set up A/B testing for {model_name}: {version_a} vs {version_b} ({traffic_split:.0%} split)")
        
        return ab_config
