"""Model drift detection service"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import logging
from sqlalchemy.orm import Session

from src.ml.model_registry import ModelRegistry
from src.models.model_registry import ModelType, ModelVersion, ModelPerformance

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    Detects model drift and triggers alerts.
    
    Monitors model performance over time and detects:
    - Performance drift (metric degradation)
    - Data drift (input distribution changes)
    - Concept drift (relationship changes)
    """
    
    # Default thresholds
    SENTIMENT_F1_THRESHOLD = 0.85
    SENTIMENT_DRIFT_THRESHOLD = 10.0  # 10% drop in F1
    
    FORECAST_MAPE_THRESHOLD = 20.0
    FORECAST_DRIFT_THRESHOLD = 10.0  # 10% increase in MAPE
    
    def __init__(self, db: Session, tenant_id: UUID):
        """
        Initialize drift detector.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
        """
        self.db = db
        self.tenant_id = tenant_id
        self.registry = ModelRegistry(db, tenant_id)
    
    def check_sentiment_drift(
        self,
        model_version_id: UUID,
        current_metrics: Dict[str, float],
        lookback_days: int = 7
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check for drift in sentiment model.
        
        Args:
            model_version_id: Model version ID
            current_metrics: Current performance metrics
            lookback_days: Days to look back for baseline
            
        Returns:
            Tuple of (drift_detected, drift_details)
        """
        # Get baseline metrics
        baseline_metrics = self._get_baseline_metrics(
            model_version_id,
            lookback_days
        )
        
        if not baseline_metrics:
            logger.warning(f"No baseline metrics found for model {model_version_id}")
            return False, []
        
        drift_details = []
        drift_detected = False
        
        # Check F1 score drift
        if 'f1_score' in current_metrics and 'f1_score' in baseline_metrics:
            current_f1 = current_metrics['f1_score']
            baseline_f1 = baseline_metrics['f1_score']
            
            # Calculate drift percentage
            drift_pct = ((baseline_f1 - current_f1) / baseline_f1) * 100
            
            # Check if drift exceeds threshold
            if drift_pct >= self.SENTIMENT_DRIFT_THRESHOLD:
                drift_detected = True
                
                # Record drift
                drift_record = self.registry.detect_drift(
                    model_version_id=model_version_id,
                    metric_name='f1_score',
                    current_value=current_f1,
                    baseline_value=baseline_f1,
                    threshold_percentage=self.SENTIMENT_DRIFT_THRESHOLD
                )
                
                if drift_record:
                    drift_details.append({
                        'metric': 'f1_score',
                        'baseline': baseline_f1,
                        'current': current_f1,
                        'drift_percentage': drift_pct,
                        'severity': drift_record.severity,
                        'drift_id': str(drift_record.id)
                    })
        
        # Check precision drift
        if 'precision' in current_metrics and 'precision' in baseline_metrics:
            current_prec = current_metrics['precision']
            baseline_prec = baseline_metrics['precision']
            
            drift_pct = ((baseline_prec - current_prec) / baseline_prec) * 100
            
            if drift_pct >= self.SENTIMENT_DRIFT_THRESHOLD:
                drift_record = self.registry.detect_drift(
                    model_version_id=model_version_id,
                    metric_name='precision',
                    current_value=current_prec,
                    baseline_value=baseline_prec,
                    threshold_percentage=self.SENTIMENT_DRIFT_THRESHOLD
                )
                
                if drift_record:
                    drift_detected = True
                    drift_details.append({
                        'metric': 'precision',
                        'baseline': baseline_prec,
                        'current': current_prec,
                        'drift_percentage': drift_pct,
                        'severity': drift_record.severity,
                        'drift_id': str(drift_record.id)
                    })
        
        # Check recall drift
        if 'recall' in current_metrics and 'recall' in baseline_metrics:
            current_rec = current_metrics['recall']
            baseline_rec = baseline_metrics['recall']
            
            drift_pct = ((baseline_rec - current_rec) / baseline_rec) * 100
            
            if drift_pct >= self.SENTIMENT_DRIFT_THRESHOLD:
                drift_record = self.registry.detect_drift(
                    model_version_id=model_version_id,
                    metric_name='recall',
                    current_value=current_rec,
                    baseline_value=baseline_rec,
                    threshold_percentage=self.SENTIMENT_DRIFT_THRESHOLD
                )
                
                if drift_record:
                    drift_detected = True
                    drift_details.append({
                        'metric': 'recall',
                        'baseline': baseline_rec,
                        'current': current_rec,
                        'drift_percentage': drift_pct,
                        'severity': drift_record.severity,
                        'drift_id': str(drift_record.id)
                    })
        
        return drift_detected, drift_details
    
    def check_forecast_drift(
        self,
        model_version_id: UUID,
        current_metrics: Dict[str, float],
        lookback_days: int = 7
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check for drift in demand forecast model.
        
        Args:
            model_version_id: Model version ID
            current_metrics: Current performance metrics
            lookback_days: Days to look back for baseline
            
        Returns:
            Tuple of (drift_detected, drift_details)
        """
        # Get baseline metrics
        baseline_metrics = self._get_baseline_metrics(
            model_version_id,
            lookback_days
        )
        
        if not baseline_metrics:
            logger.warning(f"No baseline metrics found for model {model_version_id}")
            return False, []
        
        drift_details = []
        drift_detected = False
        
        # Check MAPE drift (increase is bad for MAPE)
        if 'mape' in current_metrics and 'mape' in baseline_metrics:
            current_mape = current_metrics['mape']
            baseline_mape = baseline_metrics['mape']
            
            # For MAPE, increase is bad, so we check if current > baseline
            drift_pct = ((current_mape - baseline_mape) / baseline_mape) * 100
            
            if drift_pct >= self.FORECAST_DRIFT_THRESHOLD:
                drift_detected = True
                
                # Record drift
                drift_record = self.registry.detect_drift(
                    model_version_id=model_version_id,
                    metric_name='mape',
                    current_value=current_mape,
                    baseline_value=baseline_mape,
                    threshold_percentage=self.FORECAST_DRIFT_THRESHOLD
                )
                
                if drift_record:
                    drift_details.append({
                        'metric': 'mape',
                        'baseline': baseline_mape,
                        'current': current_mape,
                        'drift_percentage': drift_pct,
                        'severity': drift_record.severity,
                        'drift_id': str(drift_record.id)
                    })
        
        # Check RMSE drift
        if 'rmse' in current_metrics and 'rmse' in baseline_metrics:
            current_rmse = current_metrics['rmse']
            baseline_rmse = baseline_metrics['rmse']
            
            drift_pct = ((current_rmse - baseline_rmse) / baseline_rmse) * 100
            
            if drift_pct >= self.FORECAST_DRIFT_THRESHOLD:
                drift_record = self.registry.detect_drift(
                    model_version_id=model_version_id,
                    metric_name='rmse',
                    current_value=current_rmse,
                    baseline_value=baseline_rmse,
                    threshold_percentage=self.FORECAST_DRIFT_THRESHOLD
                )
                
                if drift_record:
                    drift_detected = True
                    drift_details.append({
                        'metric': 'rmse',
                        'baseline': baseline_rmse,
                        'current': current_rmse,
                        'drift_percentage': drift_pct,
                        'severity': drift_record.severity,
                        'drift_id': str(drift_record.id)
                    })
        
        return drift_detected, drift_details
    
    def check_all_models(self) -> Dict[str, Any]:
        """
        Check drift for all active models.
        
        Returns:
            Dictionary with drift status for each model type
        """
        results = {}
        
        # Check sentiment model
        sentiment_model = self.registry.get_active_model(ModelType.SENTIMENT)
        if sentiment_model:
            # Get latest performance
            latest_perf = self.registry.get_performance_history(
                sentiment_model.id,
                days=1
            )
            
            if latest_perf:
                current_metrics = latest_perf[-1].metrics
                drift_detected, drift_details = self.check_sentiment_drift(
                    sentiment_model.id,
                    current_metrics
                )
                
                results['sentiment'] = {
                    'model_id': str(sentiment_model.id),
                    'model_version': sentiment_model.version,
                    'drift_detected': drift_detected,
                    'drift_details': drift_details
                }
        
        # Check forecast model
        forecast_model = self.registry.get_active_model(ModelType.DEMAND_FORECAST)
        if forecast_model:
            # Get latest performance
            latest_perf = self.registry.get_performance_history(
                forecast_model.id,
                days=1
            )
            
            if latest_perf:
                current_metrics = latest_perf[-1].metrics
                drift_detected, drift_details = self.check_forecast_drift(
                    forecast_model.id,
                    current_metrics
                )
                
                results['demand_forecast'] = {
                    'model_id': str(forecast_model.id),
                    'model_version': forecast_model.version,
                    'drift_detected': drift_detected,
                    'drift_details': drift_details
                }
        
        return results
    
    def _get_baseline_metrics(
        self,
        model_version_id: UUID,
        lookback_days: int
    ) -> Optional[Dict[str, float]]:
        """
        Get baseline metrics by averaging over lookback period.
        
        Args:
            model_version_id: Model version ID
            lookback_days: Days to look back
            
        Returns:
            Dictionary of averaged metrics or None
        """
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Get performance records
        perf_records = self.db.query(ModelPerformance).filter(
            ModelPerformance.model_version_id == model_version_id,
            ModelPerformance.tenant_id == self.tenant_id,
            ModelPerformance.evaluation_date >= cutoff_date
        ).all()
        
        if not perf_records:
            return None
        
        # Average metrics
        metric_sums = {}
        metric_counts = {}
        
        for record in perf_records:
            for metric_name, value in record.metrics.items():
                if metric_name not in metric_sums:
                    metric_sums[metric_name] = 0.0
                    metric_counts[metric_name] = 0
                
                metric_sums[metric_name] += value
                metric_counts[metric_name] += 1
        
        # Calculate averages
        baseline_metrics = {
            metric_name: metric_sums[metric_name] / metric_counts[metric_name]
            for metric_name in metric_sums
        }
        
        return baseline_metrics
