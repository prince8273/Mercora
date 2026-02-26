"""
Model Performance Monitoring - Tracks model performance and detects drift

This module monitors ML model performance over time, detects drift,
and triggers alerts when performance degrades.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Callable
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ModelAlert:
    """Alert for model performance issues"""
    id: UUID
    model_name: str
    model_version: str
    alert_type: str  # drift, threshold_breach, evaluation_failure
    severity: AlertSeverity
    message: str
    metrics: Dict[str, float]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionRecord:
    """Record of a model prediction for tracking"""
    id: UUID
    model_name: str
    model_version: str
    prediction: Any
    actual: Optional[Any] = None
    prediction_time: datetime = field(default_factory=datetime.utcnow)
    evaluation_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelPerformanceMonitor:
    """
    Monitors ML model performance and detects drift.
    
    Tracks predictions against actuals, evaluates performance on schedule,
    and triggers alerts when drift or threshold breaches are detected.
    """
    
    # Performance thresholds
    SENTIMENT_F1_THRESHOLD = 0.85  # Minimum acceptable F1 score
    FORECAST_MAPE_THRESHOLD = 20.0  # Maximum acceptable MAPE
    
    # Drift detection thresholds
    SENTIMENT_DRIFT_THRESHOLD = 0.10  # 10% F1 drop
    FORECAST_DRIFT_THRESHOLD = 0.10  # 10% MAPE increase
    
    def __init__(self, model_registry):
        """
        Initialize model performance monitor.
        
        Args:
            model_registry: ModelRegistry instance
        """
        self.model_registry = model_registry
        self._prediction_records: List[PredictionRecord] = []
        self._alerts: List[ModelAlert] = []
        self._alert_callbacks: List[Callable[[ModelAlert], None]] = []
        self._baseline_performance: Dict[str, Dict[str, float]] = {}  # model_name -> {metric -> value}
        logger.info("ModelPerformanceMonitor initialized")
    
    def track_prediction(
        self,
        model_name: str,
        model_version: str,
        prediction: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Track a model prediction for later evaluation.
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            prediction: The prediction made
            metadata: Optional metadata (input features, confidence, etc.)
            
        Returns:
            UUID of the prediction record
        """
        record = PredictionRecord(
            id=uuid4(),
            model_name=model_name,
            model_version=model_version,
            prediction=prediction,
            metadata=metadata or {}
        )
        
        self._prediction_records.append(record)
        logger.debug(f"Tracked prediction for {model_name} v{model_version}")
        
        return record.id
    
    def record_actual(
        self,
        prediction_id: UUID,
        actual: Any
    ) -> bool:
        """
        Record the actual outcome for a prediction.
        
        Args:
            prediction_id: UUID of the prediction record
            actual: The actual outcome
            
        Returns:
            True if successful, False if prediction not found
        """
        for record in self._prediction_records:
            if record.id == prediction_id:
                record.actual = actual
                record.evaluation_time = datetime.utcnow()
                logger.debug(f"Recorded actual for prediction {prediction_id}")
                return True
        
        logger.warning(f"Prediction {prediction_id} not found")
        return False
    
    def evaluate_model_performance(
        self,
        model_name: str,
        model_version: Optional[str] = None,
        evaluation_date: Optional[date] = None
    ) -> Dict[str, float]:
        """
        Evaluate model performance based on tracked predictions.
        
        Args:
            model_name: Name of the model
            model_version: Optional version (defaults to active version)
            evaluation_date: Date to evaluate (defaults to today)
            
        Returns:
            Dictionary of performance metrics
        """
        eval_date = evaluation_date or date.today()
        
        # Get model version
        if model_version is None:
            active_model = self.model_registry.get_active_model(model_name)
            if not active_model:
                logger.error(f"No active model found for {model_name}")
                return {}
            model_version = active_model.version
        
        # Get predictions with actuals - CRITICAL: use .date() for comparison
        records = [
            r for r in self._prediction_records
            if r.model_name == model_name
            and r.model_version == model_version
            and r.actual is not None
            and r.evaluation_time is not None
            and r.evaluation_time.date() == eval_date  # ⚠️ CRITICAL: .date() comparison
        ]
        
        if not records:
            logger.warning(f"No evaluated predictions found for {model_name} v{model_version} on {eval_date}")
            return {}
        
        # Calculate metrics based on model type
        metrics = self._calculate_metrics(model_name, records)
        
        # Record performance in registry
        if metrics:  # Only record if we have metrics
            self.model_registry.record_model_performance(
                model_name=model_name,
                version=model_version,
                metrics=metrics,
                evaluation_date=eval_date
            )
        
        logger.info(f"Evaluated {model_name} v{model_version}: {metrics}")
        
        return metrics
    
    def _calculate_metrics(
        self,
        model_name: str,
        records: List[PredictionRecord]
    ) -> Dict[str, float]:
        """
        Calculate performance metrics based on model type.
        
        Args:
            model_name: Name of the model
            records: List of prediction records with actuals
            
        Returns:
            Dictionary of metrics
        """
        # Determine model type from name
        if "sentiment" in model_name.lower():
            return self._calculate_classification_metrics(records)
        elif "forecast" in model_name.lower() or "demand" in model_name.lower():
            return self._calculate_regression_metrics(records)
        else:
            logger.warning(f"Unknown model type for {model_name}, using generic metrics")
            return self._calculate_generic_metrics(records)
    
    def _calculate_classification_metrics(
        self,
        records: List[PredictionRecord]
    ) -> Dict[str, float]:
        """Calculate classification metrics (F1, precision, recall, accuracy)"""
        # Simple implementation - assumes binary or multi-class classification
        correct = sum(1 for r in records if r.prediction == r.actual)
        total = len(records)
        
        accuracy = correct / total if total > 0 else 0.0
        
        # Simplified F1 calculation (would need true/false positives for real F1)
        # For demonstration, using accuracy as proxy
        f1_score = accuracy
        
        return {
            "accuracy": round(accuracy, 4),
            "f1_score": round(f1_score, 4),
            "sample_count": total
        }
    
    def _calculate_regression_metrics(
        self,
        records: List[PredictionRecord]
    ) -> Dict[str, float]:
        """Calculate regression metrics (MAPE, MAE, RMSE)"""
        import math
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        mape_sum = 0.0
        mae_sum = 0.0
        mse_sum = 0.0
        valid_count = 0
        
        for record in records:
            try:
                pred = float(record.prediction)
                actual = float(record.actual)
                
                if actual != 0:
                    mape_sum += abs((actual - pred) / actual)
                    valid_count += 1
                
                mae_sum += abs(actual - pred)
                mse_sum += (actual - pred) ** 2
            except (ValueError, TypeError):
                logger.warning(f"Invalid prediction/actual values: {record.prediction}, {record.actual}")
                continue
        
        total = len(records)
        mape = (mape_sum / valid_count * 100) if valid_count > 0 else 0.0
        mae = mae_sum / total if total > 0 else 0.0
        rmse = math.sqrt(mse_sum / total) if total > 0 else 0.0
        
        return {
            "mape": round(mape, 4),
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "sample_count": total
        }
    
    def _calculate_generic_metrics(
        self,
        records: List[PredictionRecord]
    ) -> Dict[str, float]:
        """Calculate generic metrics when model type is unknown"""
        correct = sum(1 for r in records if r.prediction == r.actual)
        total = len(records)
        
        accuracy = correct / total if total > 0 else 0.0
        
        return {
            "accuracy": round(accuracy, 4),
            "sample_count": total
        }
    
    def detect_drift(
        self,
        model_name: str,
        model_version: str,
        current_metrics: Dict[str, float]
    ) -> List[ModelAlert]:
        """
        Detect model drift by comparing current metrics to baseline.
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            current_metrics: Current performance metrics
            
        Returns:
            List of alerts if drift detected
        """
        alerts = []
        
        # Get baseline performance
        baseline = self._baseline_performance.get(model_name, {})
        
        if not baseline:
            # No baseline yet, set current as baseline
            self._baseline_performance[model_name] = current_metrics.copy()
            logger.info(f"Set baseline performance for {model_name}: {current_metrics}")
            return alerts
        
        # Check for drift based on model type
        if "sentiment" in model_name.lower():
            alerts.extend(self._check_sentiment_drift(
                model_name, model_version, current_metrics, baseline
            ))
        elif "forecast" in model_name.lower() or "demand" in model_name.lower():
            alerts.extend(self._check_forecast_drift(
                model_name, model_version, current_metrics, baseline
            ))
        
        return alerts
    
    def _check_sentiment_drift(
        self,
        model_name: str,
        model_version: str,
        current: Dict[str, float],
        baseline: Dict[str, float]
    ) -> List[ModelAlert]:
        """Check for drift in sentiment model (F1 score drop >10%)"""
        alerts = []
        
        current_f1 = current.get("f1_score", 0.0)
        baseline_f1 = baseline.get("f1_score", 0.0)
        
        if baseline_f1 == 0:
            return alerts
        
        f1_drop = (baseline_f1 - current_f1) / baseline_f1
        
        if f1_drop > self.SENTIMENT_DRIFT_THRESHOLD:
            alert = ModelAlert(
                id=uuid4(),
                model_name=model_name,
                model_version=model_version,
                alert_type="drift",
                severity=AlertSeverity.WARNING,
                message=f"Sentiment model drift detected: F1 score dropped {f1_drop*100:.1f}% from baseline",
                metrics={
                    "current_f1": current_f1,
                    "baseline_f1": baseline_f1,
                    "f1_drop_percent": f1_drop * 100
                },
                timestamp=datetime.utcnow()
            )
            alerts.append(alert)
            self._trigger_alert(alert)
        
        return alerts
    
    def _check_forecast_drift(
        self,
        model_name: str,
        model_version: str,
        current: Dict[str, float],
        baseline: Dict[str, float]
    ) -> List[ModelAlert]:
        """Check for drift in forecast model (MAPE increase >10%)"""
        alerts = []
        
        current_mape = current.get("mape", 0.0)
        baseline_mape = baseline.get("mape", 0.0)
        
        if baseline_mape == 0:
            return alerts
        
        mape_increase = (current_mape - baseline_mape) / baseline_mape
        
        if mape_increase > self.FORECAST_DRIFT_THRESHOLD:
            alert = ModelAlert(
                id=uuid4(),
                model_name=model_name,
                model_version=model_version,
                alert_type="drift",
                severity=AlertSeverity.WARNING,
                message=f"Forecast model drift detected: MAPE increased {mape_increase*100:.1f}% from baseline",
                metrics={
                    "current_mape": current_mape,
                    "baseline_mape": baseline_mape,
                    "mape_increase_percent": mape_increase * 100
                },
                timestamp=datetime.utcnow()
            )
            alerts.append(alert)
            self._trigger_alert(alert)
        
        return alerts
    
    def check_performance_thresholds(
        self,
        model_name: str,
        model_version: str,
        metrics: Dict[str, float]
    ) -> List[ModelAlert]:
        """
        Check if performance falls below acceptable thresholds.
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            metrics: Performance metrics
            
        Returns:
            List of alerts if thresholds breached
        """
        alerts = []
        
        # Check sentiment model threshold
        if "sentiment" in model_name.lower():
            f1_score = metrics.get("f1_score", 0.0)
            if f1_score < self.SENTIMENT_F1_THRESHOLD:
                alert = ModelAlert(
                    id=uuid4(),
                    model_name=model_name,
                    model_version=model_version,
                    alert_type="threshold_breach",
                    severity=AlertSeverity.CRITICAL,
                    message=f"Sentiment model F1 score ({f1_score:.3f}) below threshold ({self.SENTIMENT_F1_THRESHOLD})",
                    metrics={"f1_score": f1_score, "threshold": self.SENTIMENT_F1_THRESHOLD},
                    timestamp=datetime.utcnow()
                )
                alerts.append(alert)
                self._trigger_alert(alert)
        
        # Check forecast model threshold
        elif "forecast" in model_name.lower() or "demand" in model_name.lower():
            mape = metrics.get("mape", 0.0)
            if mape > self.FORECAST_MAPE_THRESHOLD:
                alert = ModelAlert(
                    id=uuid4(),
                    model_name=model_name,
                    model_version=model_version,
                    alert_type="threshold_breach",
                    severity=AlertSeverity.CRITICAL,
                    message=f"Forecast model MAPE ({mape:.2f}%) above threshold ({self.FORECAST_MAPE_THRESHOLD}%)",
                    metrics={"mape": mape, "threshold": self.FORECAST_MAPE_THRESHOLD},
                    timestamp=datetime.utcnow()
                )
                alerts.append(alert)
                self._trigger_alert(alert)
        
        return alerts
    
    def register_alert_callback(self, callback: Callable[[ModelAlert], None]) -> None:
        """
        Register a callback to be invoked when alerts are triggered.
        
        Args:
            callback: Function to call with ModelAlert
        """
        self._alert_callbacks.append(callback)
        logger.info(f"Registered alert callback: {callback.__name__}")
    
    def _trigger_alert(self, alert: ModelAlert) -> None:
        """Trigger alert callbacks"""
        self._alerts.append(alert)
        logger.warning(f"Alert triggered: {alert.message}")
        
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def get_alerts(
        self,
        model_name: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 100
    ) -> List[ModelAlert]:
        """
        Get recent alerts.
        
        Args:
            model_name: Optional filter by model name
            severity: Optional filter by severity
            limit: Maximum number of alerts to return
            
        Returns:
            List of ModelAlert objects, sorted by timestamp (newest first)
        """
        alerts = [
            a for a in self._alerts
            if (model_name is None or a.model_name == model_name)
            and (severity is None or a.severity == severity)
        ]
        
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return alerts[:limit]
    
    def set_baseline_performance(
        self,
        model_name: str,
        metrics: Dict[str, float]
    ) -> None:
        """
        Manually set baseline performance for a model.
        
        Args:
            model_name: Name of the model
            metrics: Baseline performance metrics
        """
        self._baseline_performance[model_name] = metrics.copy()
        logger.info(f"Set baseline performance for {model_name}: {metrics}")
    
    def get_baseline_performance(self, model_name: str) -> Dict[str, float]:
        """
        Get baseline performance for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Baseline metrics or empty dict if not set
        """
        return self._baseline_performance.get(model_name, {}).copy()
