"""Model retraining workflow service"""
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import logging
from sqlalchemy.orm import Session

from src.ml.model_registry import ModelRegistry
from src.ml.drift_detector import DriftDetector
from src.models.model_registry import ModelType, RetrainingJob

logger = logging.getLogger(__name__)


class RetrainingService:
    """
    Manages automated model retraining workflows.
    
    Responsibilities:
    - Monitor model performance
    - Trigger retraining when needed
    - Coordinate retraining jobs
    - Version new models
    - A/B testing support
    """
    
    def __init__(self, db: Session, tenant_id: UUID):
        """
        Initialize retraining service.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
        """
        self.db = db
        self.tenant_id = tenant_id
        self.registry = ModelRegistry(db, tenant_id)
        self.drift_detector = DriftDetector(db, tenant_id)
    
    def check_and_trigger_retraining(self) -> Dict[str, Any]:
        """
        Check all models and trigger retraining if needed.
        
        Returns:
            Dictionary with retraining status for each model type
        """
        results = {}
        
        # Check sentiment model
        sentiment_needed = self.registry.check_retraining_needed(
            ModelType.SENTIMENT,
            sentiment_f1_threshold=0.85
        )
        
        if sentiment_needed:
            job = self.registry.trigger_retraining(
                model_type=ModelType.SENTIMENT,
                trigger_reason="performance_below_threshold"
            )
            results['sentiment'] = {
                'retraining_triggered': True,
                'job_id': str(job.id),
                'reason': 'performance_below_threshold'
            }
            logger.info(f"Triggered sentiment model retraining (job_id={job.id})")
        else:
            results['sentiment'] = {
                'retraining_triggered': False,
                'reason': 'performance_acceptable'
            }
        
        # Check forecast model
        forecast_needed = self.registry.check_retraining_needed(
            ModelType.DEMAND_FORECAST,
            forecast_mape_threshold=20.0
        )
        
        if forecast_needed:
            job = self.registry.trigger_retraining(
                model_type=ModelType.DEMAND_FORECAST,
                trigger_reason="performance_below_threshold"
            )
            results['demand_forecast'] = {
                'retraining_triggered': True,
                'job_id': str(job.id),
                'reason': 'performance_below_threshold'
            }
            logger.info(f"Triggered forecast model retraining (job_id={job.id})")
        else:
            results['demand_forecast'] = {
                'retraining_triggered': False,
                'reason': 'performance_acceptable'
            }
        
        return results
    
    def trigger_retraining_on_drift(self) -> Dict[str, Any]:
        """
        Check for drift and trigger retraining if detected.
        
        Returns:
            Dictionary with drift and retraining status
        """
        # Check drift for all models
        drift_results = self.drift_detector.check_all_models()
        
        retraining_results = {}
        
        # Trigger retraining for models with drift
        for model_type_str, drift_info in drift_results.items():
            if drift_info['drift_detected']:
                # Map string to ModelType enum
                if model_type_str == 'sentiment':
                    model_type = ModelType.SENTIMENT
                elif model_type_str == 'demand_forecast':
                    model_type = ModelType.DEMAND_FORECAST
                else:
                    continue
                
                # Trigger retraining
                job = self.registry.trigger_retraining(
                    model_type=model_type,
                    trigger_reason="drift_detected",
                    training_config={
                        'drift_details': drift_info['drift_details']
                    }
                )
                
                retraining_results[model_type_str] = {
                    'drift_detected': True,
                    'retraining_triggered': True,
                    'job_id': str(job.id),
                    'drift_details': drift_info['drift_details']
                }
                
                logger.warning(
                    f"Drift detected for {model_type_str} model, "
                    f"triggered retraining (job_id={job.id})"
                )
            else:
                retraining_results[model_type_str] = {
                    'drift_detected': False,
                    'retraining_triggered': False
                }
        
        return retraining_results
    
    def execute_retraining_job(
        self,
        job_id: UUID,
        training_function: callable
    ) -> Dict[str, Any]:
        """
        Execute a retraining job.
        
        Args:
            job_id: Retraining job ID
            training_function: Function that performs the actual training
                              Should accept (model_type, training_config) and return
                              (model_path, metrics, hyperparameters)
            
        Returns:
            Dictionary with execution results
        """
        # Get job
        job = self.db.query(RetrainingJob).filter(
            RetrainingJob.id == job_id,
            RetrainingJob.tenant_id == self.tenant_id
        ).first()
        
        if not job:
            raise ValueError(f"Retraining job {job_id} not found")
        
        # Update job status
        job.status = "running"
        job.started_at = datetime.utcnow()
        self.db.commit()
        
        try:
            # Execute training
            logger.info(f"Starting retraining job {job_id} for {job.model_type}")
            
            model_path, metrics, hyperparameters = training_function(
                job.model_type,
                job.training_config
            )
            
            # Calculate duration
            duration = (datetime.utcnow() - job.started_at).total_seconds()
            
            # Generate version string
            version = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            
            # Register new model version
            new_model = self.registry.register_model(
                model_type=job.model_type,
                model_name=f"{job.model_type.value}_model",
                version=version,
                framework="transformers" if job.model_type == ModelType.SENTIMENT else "prophet",
                algorithm="distilbert" if job.model_type == ModelType.SENTIMENT else "prophet",
                model_path=model_path,
                metrics=metrics,
                hyperparameters=hyperparameters,
                training_duration_seconds=duration
            )
            
            # Update job
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.duration_seconds = duration
            job.new_model_version_id = new_model.id
            job.metrics = metrics
            self.db.commit()
            
            logger.info(
                f"Completed retraining job {job_id}, "
                f"created model version {new_model.version}"
            )
            
            return {
                'success': True,
                'job_id': str(job_id),
                'new_model_id': str(new_model.id),
                'new_model_version': new_model.version,
                'metrics': metrics,
                'duration_seconds': duration
            }
            
        except Exception as e:
            # Update job with error
            job.status = "failed"
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            self.db.commit()
            
            logger.error(f"Retraining job {job_id} failed: {str(e)}")
            
            return {
                'success': False,
                'job_id': str(job_id),
                'error': str(e)
            }
    
    def compare_models_ab_test(
        self,
        model_a_id: UUID,
        model_b_id: UUID,
        test_data_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Compare two model versions using A/B testing.
        
        Args:
            model_a_id: First model version ID
            model_b_id: Second model version ID
            test_data_size: Size of test dataset
            
        Returns:
            Comparison results
        """
        # Get models
        model_a = self.db.query(ModelVersion).filter(
            ModelVersion.id == model_a_id,
            ModelVersion.tenant_id == self.tenant_id
        ).first()
        
        model_b = self.db.query(ModelVersion).filter(
            ModelVersion.id == model_b_id,
            ModelVersion.tenant_id == self.tenant_id
        ).first()
        
        if not model_a or not model_b:
            raise ValueError("One or both models not found")
        
        if model_a.model_type != model_b.model_type:
            raise ValueError("Models must be of the same type")
        
        # Get latest performance for both models
        perf_a = self.registry.get_performance_history(model_a_id, days=7)
        perf_b = self.registry.get_performance_history(model_b_id, days=7)
        
        if not perf_a or not perf_b:
            return {
                'error': 'Insufficient performance data for comparison',
                'model_a_records': len(perf_a) if perf_a else 0,
                'model_b_records': len(perf_b) if perf_b else 0
            }
        
        # Average metrics
        avg_metrics_a = self._average_metrics([p.metrics for p in perf_a])
        avg_metrics_b = self._average_metrics([p.metrics for p in perf_b])
        
        # Compare metrics
        comparison = {
            'model_a': {
                'id': str(model_a_id),
                'version': model_a.version,
                'metrics': avg_metrics_a
            },
            'model_b': {
                'id': str(model_b_id),
                'version': model_b.version,
                'metrics': avg_metrics_b
            },
            'winner': None,
            'improvements': {}
        }
        
        # Determine winner based on primary metric
        if model_a.model_type == ModelType.SENTIMENT:
            primary_metric = 'f1_score'
            if avg_metrics_a.get(primary_metric, 0) > avg_metrics_b.get(primary_metric, 0):
                comparison['winner'] = 'model_a'
            else:
                comparison['winner'] = 'model_b'
        elif model_a.model_type == ModelType.DEMAND_FORECAST:
            primary_metric = 'mape'
            if avg_metrics_a.get(primary_metric, float('inf')) < avg_metrics_b.get(primary_metric, float('inf')):
                comparison['winner'] = 'model_a'
            else:
                comparison['winner'] = 'model_b'
        
        # Calculate improvements
        for metric in avg_metrics_a:
            if metric in avg_metrics_b:
                val_a = avg_metrics_a[metric]
                val_b = avg_metrics_b[metric]
                if val_a != 0:
                    improvement = ((val_b - val_a) / abs(val_a)) * 100
                    comparison['improvements'][metric] = improvement
        
        return comparison
    
    def _average_metrics(self, metrics_list: list) -> Dict[str, float]:
        """Average a list of metric dictionaries."""
        if not metrics_list:
            return {}
        
        metric_sums = {}
        metric_counts = {}
        
        for metrics in metrics_list:
            for metric_name, value in metrics.items():
                if metric_name not in metric_sums:
                    metric_sums[metric_name] = 0.0
                    metric_counts[metric_name] = 0
                
                metric_sums[metric_name] += value
                metric_counts[metric_name] += 1
        
        return {
            metric_name: metric_sums[metric_name] / metric_counts[metric_name]
            for metric_name in metric_sums
        }
