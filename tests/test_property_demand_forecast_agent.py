"""
Property-Based Tests for Demand Forecast Agent

These tests validate correctness properties for demand forecasting functionality
using Hypothesis for property-based testing.
"""
import pytest
from hypothesis import given, strategies as st, settings
from uuid import uuid4
from datetime import datetime, timedelta

from src.agents.demand_forecast_agent import DemandForecastAgent


class TestDemandForecastProperties:
    """Property-based tests for Demand Forecast Agent"""
    
    @settings(max_examples=10, deadline=None)
    @given(
        forecast_horizon=st.integers(min_value=7, max_value=90),
        num_data_points=st.integers(min_value=14, max_value=60)
    )
    def test_property_21_forecasts_generated_for_configured_horizons(
        self, forecast_horizon, num_data_points
    ):
        """
        # Feature: ecommerce-intelligence-agent, Property 21: Forecasts are generated for configured horizons
        
        Property: Forecasts must be generated for the specified horizon
        (7, 30, or 90 days) with predictions for each day.
        
        Validates: Requirements 5.1
        """
        tenant_id = uuid4()
        agent = DemandForecastAgent(tenant_id)
        product_id = uuid4()
        
        # Create sales history
        sales_history = []
        start_date = datetime.now() - timedelta(days=num_data_points)
        for i in range(num_data_points):
            sales_history.append({
                'date': (start_date + timedelta(days=i)).date(),
                'quantity': 10 + (i % 5)  # Simple pattern
            })
        
        # Generate forecast
        result = agent.forecast_demand(
            product_id=product_id,
            product_name="Test Product",
            sales_history=sales_history,
            forecast_horizon_days=forecast_horizon
        )
        
        # Property: Forecast must have the correct number of points
        assert len(result.forecast_points) == forecast_horizon
        
        # Property: Each forecast point must have required fields
        for fp in result.forecast_points:
            assert hasattr(fp, 'date')
            assert hasattr(fp, 'predicted_quantity')
            assert hasattr(fp, 'lower_bound')
            assert hasattr(fp, 'upper_bound')
            assert hasattr(fp, 'confidence')
            assert fp.predicted_quantity >= 0
            assert 0.0 <= fp.confidence <= 1.0
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_data_points=st.integers(min_value=30, max_value=90)
    )
    def test_property_22_seasonal_patterns_detected_and_incorporated(
        self, num_data_points
    ):
        """
        # Feature: ecommerce-intelligence-agent, Property 22: Seasonal patterns are detected and incorporated
        
        Property: Seasonal patterns (weekly, monthly) must be detected
        and incorporated into forecasts when sufficient data exists.
        
        Validates: Requirements 5.2
        """
        tenant_id = uuid4()
        agent = DemandForecastAgent(tenant_id)
        product_id = uuid4()
        
        # Create sales history with weekly pattern
        sales_history = []
        start_date = datetime.now() - timedelta(days=num_data_points)
        for i in range(num_data_points):
            # Weekly pattern: higher sales on weekends
            day_of_week = (start_date + timedelta(days=i)).weekday()
            quantity = 20 if day_of_week >= 5 else 10
            sales_history.append({
                'date': (start_date + timedelta(days=i)).date(),
                'quantity': quantity
            })
        
        # Generate forecast
        result = agent.forecast_demand(
            product_id=product_id,
            product_name="Test Product",
            sales_history=sales_history,
            forecast_horizon_days=30
        )
        
        # Property: Seasonality must be detected
        assert hasattr(result, 'seasonality')
        assert isinstance(result.seasonality, dict)
        
        # Property: Seasonality patterns must have required fields
        for period, pattern in result.seasonality.items():
            assert hasattr(pattern, 'period')
            assert hasattr(pattern, 'strength')
            assert hasattr(pattern, 'detected')
            assert 0.0 <= pattern.strength <= 1.0
            assert isinstance(pattern.detected, bool)
    
    @settings(max_examples=10, deadline=None)
    @given(
        current_inventory=st.integers(min_value=0, max_value=100),
        avg_daily_demand=st.integers(min_value=5, max_value=20)
    )
    def test_property_23_demand_supply_imbalances_identified(
        self, current_inventory, avg_daily_demand
    ):
        """
        # Feature: ecommerce-intelligence-agent, Property 23: Demand-supply imbalances are identified
        
        Property: Demand-supply imbalances must be identified when
        inventory levels don't match forecasted demand.
        
        Validates: Requirements 5.3
        """
        tenant_id = uuid4()
        agent = DemandForecastAgent(tenant_id)
        product_id = uuid4()
        
        # Create sales history with consistent demand
        sales_history = []
        start_date = datetime.now() - timedelta(days=30)
        for i in range(30):
            sales_history.append({
                'date': (start_date + timedelta(days=i)).date(),
                'quantity': avg_daily_demand
            })
        
        # Generate forecast
        result = agent.forecast_demand(
            product_id=product_id,
            product_name="Test Product",
            sales_history=sales_history,
            forecast_horizon_days=30,
            current_inventory=current_inventory
        )
        
        # Property: Result must have alerts
        assert hasattr(result, 'alerts')
        assert isinstance(result.alerts, list)
        
        # Property: If inventory is low, stockout alerts should be present
        days_of_stock = current_inventory / (avg_daily_demand + 1)
        if days_of_stock < 14:
            # Should have at least one stockout-related alert
            alert_types = [alert.alert_type for alert in result.alerts]
            assert any(
                alert_type in ['stockout_risk', 'reorder_point']
                for alert_type in alert_types
            )
    
    @settings(max_examples=10, deadline=None)
    @given(
        current_inventory=st.integers(min_value=0, max_value=50),
        avg_daily_demand=st.integers(min_value=10, max_value=20)
    )
    def test_property_24_inventory_risks_generate_alerts(
        self, current_inventory, avg_daily_demand
    ):
        """
        # Feature: ecommerce-intelligence-agent, Property 24: Inventory risks generate alerts
        
        Property: Inventory risks (stockout, overstock) must generate
        alerts with severity levels and recommended actions.
        
        Validates: Requirements 5.4
        """
        tenant_id = uuid4()
        agent = DemandForecastAgent(tenant_id)
        product_id = uuid4()
        
        # Create sales history
        sales_history = []
        start_date = datetime.now() - timedelta(days=30)
        for i in range(30):
            sales_history.append({
                'date': (start_date + timedelta(days=i)).date(),
                'quantity': avg_daily_demand
            })
        
        # Generate forecast
        result = agent.forecast_demand(
            product_id=product_id,
            product_name="Test Product",
            sales_history=sales_history,
            forecast_horizon_days=30,
            current_inventory=current_inventory
        )
        
        # Property: Alerts must have required fields
        for alert in result.alerts:
            assert hasattr(alert, 'alert_type')
            assert hasattr(alert, 'severity')
            assert hasattr(alert, 'message')
            assert hasattr(alert, 'recommended_action')
            assert alert.severity in ['low', 'medium', 'high', 'critical']
            assert len(alert.message) > 0
            assert len(alert.recommended_action) > 0
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_data_points=st.integers(min_value=7, max_value=13),
        volatility=st.floats(min_value=0.5, max_value=2.0)
    )
    def test_property_25_low_confidence_forecasts_indicate_uncertainty(
        self, num_data_points, volatility
    ):
        """
        # Feature: ecommerce-intelligence-agent, Property 25: Low-confidence forecasts indicate uncertainty
        
        Property: Forecasts with insufficient data or high volatility
        must have low confidence scores and uncertainty indicators.
        
        Validates: Requirements 5.5
        """
        tenant_id = uuid4()
        agent = DemandForecastAgent(tenant_id)
        product_id = uuid4()
        
        # Create sales history with high volatility
        sales_history = []
        start_date = datetime.now() - timedelta(days=num_data_points)
        for i in range(num_data_points):
            # High volatility: random fluctuations
            quantity = int(10 * volatility * (1 + (i % 3) * 0.5))
            sales_history.append({
                'date': (start_date + timedelta(days=i)).date(),
                'quantity': quantity
            })
        
        # Generate forecast
        result = agent.forecast_demand(
            product_id=product_id,
            product_name="Test Product",
            sales_history=sales_history,
            forecast_horizon_days=30
        )
        
        # Property: Result must have confidence scores
        assert hasattr(result, 'base_confidence')
        assert hasattr(result, 'data_quality_score')
        assert hasattr(result, 'final_confidence')
        assert 0.0 <= result.final_confidence <= 1.0
        
        # Property: Low data points should result in lower confidence
        if num_data_points < agent.min_data_points:
            assert result.data_quality_score < 1.0
            assert 'insufficient_data' in result.qa_metadata or 'limited_data' in result.qa_metadata
        
        # Property: High volatility should be flagged
        if volatility > 0.8:
            # Should have volatility warning in QA metadata
            assert 'high_volatility' in result.qa_metadata or 'coefficient_of_variation' in result.qa_metadata
        
        # Property: QA metadata must be present
        assert hasattr(result, 'qa_metadata')
        assert isinstance(result.qa_metadata, dict)
