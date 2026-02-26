"""Property-based tests for model monitoring and registry"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, date, timedelta
from uuid import uuid4

from src.model_management import (
    ModelRegistry,
    ModelPerformanceMonitor,
    ModelStage,
    AlertSeverity
)


class TestPredictionTracking:
    """
    Property 57: Predictions are tracked against actuals
    Validates: Requirements 14.1
    """
    
    @given(
        model_name=st.text(min_size=1, max_size=50),
        model_version=st.text(min_size=1, max_size=20),
        num_predictions=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=10, deadline=None)
    def test_predictions_are_tracked(self, model_name, model_version, num_predictions):
        """Test that predictions are tracked with actuals"""
        registry = ModelRegistry()
        monitor = ModelPerformanceMonitor(registry)
        
        # Track predictions
        prediction_ids = []
        for i in range(num_predictions):
            pred_id = monitor.track_prediction(
                model_name=model_name,
                model_version=model_version,
                prediction=i % 2,  # Binary predictions
                metadata={"index": i}
            )
            prediction_ids.append(pred_id)
        
        # Property: All predictions must be tracked
        assert len(monitor._prediction_records) >= num_predictions
        
        # Record actuals
        for pred_id in prediction_ids:
            success = monitor.record_actual(pred_id, 1)
            assert success is True
        
        # Property: All predictions must have actuals recorded
        records_with_actuals = [
            r for r in monitor._prediction_records
            if r.model_name == model_name and r.actual is not None
        ]
        assert len(records_with_actuals) >= num_predictions


class TestScheduledEvaluation:
    """
    Property 58: Model performance is evaluated on schedule
    Validates: Requirements 14.2
    """
    
    @given(
        model_name=st.text(min_size=1, max_size=50),
        model_version=st.text(min_size=1, max_size=20),
        num_days=st.integers(min_value=1, max_value=7)
    )
    @settings(max_examples=10, deadline=None)
    def test_scheduled_evaluation_occurs(self, model_name, model_version, num_days):
        """Test that model performance is evaluated on schedule"""
        registry = ModelRegistry()
        monitor = ModelPerformanceMonitor(registry)
        
        # Register model
        registry.register_model(
            model_name=model_name,
            model_version=model_version,
            model_artifact_path="/path/to/model"
        )
        
        # Track predictions for multiple days
        for day_offset in range(num_days):
            eval_date = date.today() - timedelta(days=day_offset)
            
            # Track some predictions
            for i in range(5):
                pred_id = monitor.track_prediction(
                    model_name=model_name,
                    model_version=model_version,
                    prediction=i % 2
                )
                monitor.record_actual(pred_id, i % 2)
                
                # Set evaluation time to the target date
                for record in monitor._prediction_records:
                    if record.id == pred_id:
                        record.evaluation_time = datetime.combine(eval_date, datetime.min.time())
            
            # Evaluate performance for this day
            metrics = monitor.evaluate_model_performance(
                model_name=model_name,
                model_version=model_version,
                evaluation_date=eval_date
            )
            
            # Property: Evaluation must produce metrics
            assert len(metrics) > 0
            assert "sample_count" in metrics
        
        # Property: Performance history must be recorded
        history = registry.get_performance_history(model_name, model_version)
        assert len(history) >= num_days


class TestDriftAlertTriggering:
    """
    Property 59: Model drift triggers alerts
    Validates: Requirements 14.3, 14.4
    """
    
    @given(
        model_type=st.sampled_from(["sentiment_classifier", "demand_forecast"]),
        drift_magnitude=st.floats(min_value=0.11, max_value=0.50)
    )
    @settings(max_examples=10, deadline=None)
    def test_drift_triggers_alerts(self, model_type, drift_magnitude):
        """Test that model drift triggers alerts"""
        registry = ModelRegistry()
        monitor = ModelPerformanceMonitor(registry)
        model_version = "1.0.0"
        
        # Set baseline performance
        if "sentiment" in model_type:
            baseline = {"f1_score": 0.90, "accuracy": 0.90}
            # Create degraded performance (F1 drop > 10%)
            current = {"f1_score": 0.90 * (1 - drift_magnitude), "accuracy": 0.85}
        else:  # forecast
            baseline = {"mape": 10.0, "mae": 5.0}
            # Create degraded performance (MAPE increase > 10%)
            current = {"mape": 10.0 * (1 + drift_magnitude), "mae": 6.0}
        
        monitor.set_baseline_performance(model_type, baseline)
        
        # Detect drift
        alerts = monitor.detect_drift(model_type, model_version, current)
        
        # Property: Drift must trigger alerts
        assert len(alerts) > 0
        
        # Property: Alert must be of type "drift"
        assert all(alert.alert_type == "drift" for alert in alerts)
        
        # Property: Alert severity must be WARNING
        assert all(alert.severity == AlertSeverity.WARNING for alert in alerts)
        
        # Property: Alert must contain relevant metrics
        for alert in alerts:
            assert "baseline" in alert.message.lower() or len(alert.metrics) > 0


class TestRetrainingTrigger:
    """
    Property 60: Poor performance triggers retraining
    Validates: Requirements 14.5
    """
    
    @given(
        model_type=st.sampled_from(["sentiment_classifier", "demand_forecast"])
    )
    @settings(max_examples=10, deadline=None)
    def test_poor_performance_triggers_alert(self, model_type):
        """Test that performance below threshold triggers critical alerts"""
        registry = ModelRegistry()
        monitor = ModelPerformanceMonitor(registry)
        model_version = "1.0.0"
        
        # Create performance below threshold
        if "sentiment" in model_type:
            # F1 < 0.85
            metrics = {"f1_score": 0.80, "accuracy": 0.80}
        else:  # forecast
            # MAPE > 20%
            metrics = {"mape": 25.0, "mae": 10.0}
        
        # Check thresholds
        alerts = monitor.check_performance_thresholds(
            model_name=model_type,
            model_version=model_version,
            metrics=metrics
        )
        
        # Property: Poor performance must trigger alerts
        assert len(alerts) > 0
        
        # Property: Alert must be CRITICAL severity (triggers retraining)
        assert all(alert.severity == AlertSeverity.CRITICAL for alert in alerts)
        
        # Property: Alert type must be threshold_breach
        assert all(alert.alert_type == "threshold_breach" for alert in alerts)


class TestModelVersioning:
    """
    Property 61: Model retraining creates versions
    Validates: Requirements 14.6
    """
    
    @given(
        model_name=st.text(min_size=1, max_size=50),
        num_versions=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_model_versioning(self, model_name, num_versions):
        """Test that model retraining creates new versions"""
        registry = ModelRegistry()
        
        # Register multiple versions (simulating retraining)
        versions = []
        for i in range(num_versions):
            version = f"v{i+1}.0.0"
            registration = registry.register_model(
                model_name=model_name,
                model_version=version,
                model_artifact_path=f"/path/to/model/{version}",
                metadata={"retrain_iteration": i}
            )
            versions.append(version)
        
        # Property: All versions must be registered
        registered_versions = registry.list_model_versions(model_name)
        assert len(registered_versions) == num_versions
        
        # Property: Each version must be unique
        version_strings = [v.version for v in registered_versions]
        assert len(set(version_strings)) == num_versions
        
        # Property: Latest version must be retrievable
        latest = registry.get_latest_version(model_name)
        assert latest is not None
        assert latest.version in versions
        
        # Property: Performance history can be tracked per version
        for version in versions:
            registry.record_model_performance(
                model_name=model_name,
                version=version,
                metrics={"accuracy": 0.85 + (versions.index(version) * 0.01)}
            )
        
        # Each version should have performance records
        for version in versions:
            history = registry.get_performance_history(model_name, version)
            assert len(history) > 0


class TestModelPromotion:
    """Additional tests for model promotion and staging"""
    
    @given(
        model_name=st.text(min_size=1, max_size=50),
        model_version=st.text(min_size=1, max_size=20)
    )
    @settings(max_examples=10, deadline=None)
    def test_model_promotion_workflow(self, model_name, model_version):
        """Test model promotion through stages"""
        registry = ModelRegistry()
        
        # Register model (starts in DEVELOPMENT)
        registry.register_model(
            model_name=model_name,
            model_version=model_version,
            model_artifact_path="/path/to/model"
        )
        
        model = registry.get_model_by_version(model_name, model_version)
        assert model.stage == ModelStage.DEVELOPMENT
        
        # Promote to STAGING
        registry.promote_model(model_name, model_version, "staging")
        model = registry.get_model_by_version(model_name, model_version)
        assert model.stage == ModelStage.STAGING
        
        # Promote to PRODUCTION
        registry.promote_model(model_name, model_version, "production")
        model = registry.get_model_by_version(model_name, model_version)
        assert model.stage == ModelStage.PRODUCTION
        
        # Property: Production model must be active
        active = registry.get_active_model(model_name)
        assert active is not None
        assert active.version == model_version


class TestPerformanceHistory:
    """Additional tests for performance history tracking"""
    
    @given(
        model_name=st.text(min_size=1, max_size=50),
        model_version=st.text(min_size=1, max_size=20),
        num_evaluations=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_performance_history_tracking(self, model_name, model_version, num_evaluations):
        """Test that performance history is tracked over time"""
        registry = ModelRegistry()
        
        # Register model
        registry.register_model(
            model_name=model_name,
            model_version=model_version,
            model_artifact_path="/path/to/model"
        )
        
        # Record performance over multiple evaluations
        for i in range(num_evaluations):
            eval_date = date.today() - timedelta(days=i)
            metrics = {
                "accuracy": 0.85 + (i * 0.01),
                "f1_score": 0.83 + (i * 0.01)
            }
            registry.record_model_performance(
                model_name=model_name,
                version=model_version,
                metrics=metrics,
                evaluation_date=eval_date
            )
        
        # Property: All evaluations must be in history
        history = registry.get_performance_history(model_name, model_version)
        assert len(history) >= num_evaluations * 2  # 2 metrics per evaluation
        
        # Property: History must be sorted by date (newest first)
        dates = [record.evaluation_date for record in history]
        assert dates == sorted(dates, reverse=True)


class TestAlertCallbacks:
    """Additional tests for alert callback system"""
    
    @given(
        model_name=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=10, deadline=None)
    def test_alert_callbacks_invoked(self, model_name):
        """Test that alert callbacks are invoked when alerts trigger"""
        registry = ModelRegistry()
        monitor = ModelPerformanceMonitor(registry)
        
        # Track callback invocations
        callback_invocations = []
        
        def alert_callback(alert):
            callback_invocations.append(alert)
        
        monitor.register_alert_callback(alert_callback)
        
        # Trigger an alert by checking poor performance
        metrics = {"f1_score": 0.70}  # Below threshold
        alerts = monitor.check_performance_thresholds(
            model_name=f"{model_name}_sentiment",
            model_version="1.0.0",
            metrics=metrics
        )
        
        # Property: Callback must be invoked for each alert
        assert len(callback_invocations) == len(alerts)
        
        # Property: Callback receives correct alert objects
        for alert in callback_invocations:
            assert alert.model_name == f"{model_name}_sentiment"
            assert alert.severity == AlertSeverity.CRITICAL


class TestMetricsCalculation:
    """Additional tests for metrics calculation"""
    
    def test_classification_metrics_calculation(self):
        """Test classification metrics are calculated correctly"""
        registry = ModelRegistry()
        monitor = ModelPerformanceMonitor(registry)
        model_name = "sentiment_classifier"
        model_version = "1.0.0"
        
        registry.register_model(model_name, model_version, "/path/to/model")
        
        # Track predictions with known accuracy
        correct_predictions = 8
        total_predictions = 10
        eval_date = date.today()
        
        for i in range(total_predictions):
            pred = 1 if i < correct_predictions else 0
            actual = 1 if i < correct_predictions else 1  # Last 2 are wrong
            
            pred_id = monitor.track_prediction(model_name, model_version, pred)
            monitor.record_actual(pred_id, actual)
            
            # Set evaluation time to today
            for record in monitor._prediction_records:
                if record.id == pred_id:
                    record.evaluation_time = datetime.combine(eval_date, datetime.min.time())
        
        # Evaluate
        metrics = monitor.evaluate_model_performance(model_name, model_version, eval_date)
        
        # Property: Accuracy must be calculated
        assert "accuracy" in metrics
        assert metrics["accuracy"] == correct_predictions / total_predictions
    
    def test_regression_metrics_calculation(self):
        """Test regression metrics are calculated correctly"""
        registry = ModelRegistry()
        monitor = ModelPerformanceMonitor(registry)
        model_name = "demand_forecast"
        model_version = "1.0.0"
        
        registry.register_model(model_name, model_version, "/path/to/model")
        
        # Track predictions with known errors
        predictions = [100, 200, 300]
        actuals = [110, 190, 310]
        eval_date = date.today()
        
        for pred, actual in zip(predictions, actuals):
            pred_id = monitor.track_prediction(model_name, model_version, pred)
            monitor.record_actual(pred_id, actual)
            
            # Set evaluation time to today
            for record in monitor._prediction_records:
                if record.id == pred_id:
                    record.evaluation_time = datetime.combine(eval_date, datetime.min.time())
        
        # Evaluate
        metrics = monitor.evaluate_model_performance(model_name, model_version, eval_date)
        
        # Property: MAPE must be calculated
        assert "mape" in metrics
        assert metrics["mape"] > 0
        
        # Property: MAE must be calculated
        assert "mae" in metrics
        assert metrics["mae"] > 0
