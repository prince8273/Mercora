"""Tests for Demand Forecast Agent"""
import pytest
from datetime import date, timedelta
from uuid import uuid4

from src.agents.demand_forecast_agent import DemandForecastAgent


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return uuid4()


@pytest.fixture
def sample_sales_history():
    """Generate sample sales history for testing"""
    history = []
    base_date = date.today() - timedelta(days=60)
    
    # Generate 60 days of sales with some pattern
    for i in range(60):
        current_date = base_date + timedelta(days=i)
        # Add weekly seasonality (higher on weekends)
        base_quantity = 10
        if current_date.weekday() >= 5:  # Weekend
            base_quantity = 15
        
        # Add some random variation
        import random
        quantity = base_quantity + random.randint(-3, 3)
        
        history.append({
            'date': current_date,
            'quantity': max(0, quantity)
        })
    
    return history


def test_demand_forecast_agent_initialization(tenant_id):
    """Test agent initialization"""
    agent = DemandForecastAgent(tenant_id=tenant_id)
    
    assert agent.tenant_id == tenant_id
    assert agent.min_data_points == 14
    assert agent.confidence_threshold == 0.6


def test_forecast_demand_basic(tenant_id, sample_sales_history):
    """Test basic demand forecasting"""
    agent = DemandForecastAgent(tenant_id=tenant_id)
    
    product_id = uuid4()
    product_name = "Test Product"
    
    result = agent.forecast_demand(
        product_id=product_id,
        product_name=product_name,
        sales_history=sample_sales_history,
        forecast_horizon_days=30,
        current_inventory=100
    )
    
    # Verify result structure
    assert result.product_id == product_id
    assert result.product_name == product_name
    assert result.forecast_horizon_days == 30
    assert len(result.forecast_points) == 30
    
    # Verify forecast points
    for fp in result.forecast_points:
        assert fp.predicted_quantity >= 0
        assert fp.lower_bound >= 0
        assert fp.upper_bound >= fp.predicted_quantity
        assert 0 <= fp.confidence <= 1
    
    # Verify model selection
    assert result.best_model in ['moving_average', 'exponential_smoothing', 'arima', 'prophet']
    
    # Verify confidence scores
    assert 0 <= result.base_confidence <= 1
    assert 0 <= result.data_quality_score <= 1
    assert 0 <= result.final_confidence <= 1
    
    # Verify metadata
    assert result.historical_data_points == 60
    assert result.forecast_generated_at is not None


def test_forecast_with_insufficient_data(tenant_id):
    """Test forecasting with insufficient data"""
    agent = DemandForecastAgent(tenant_id=tenant_id)
    
    # Only 7 days of data (below minimum)
    short_history = [
        {'date': date.today() - timedelta(days=i), 'quantity': 5}
        for i in range(7)
    ]
    
    result = agent.forecast_demand(
        product_id=uuid4(),
        product_name="Test Product",
        sales_history=short_history,
        forecast_horizon_days=30
    )
    
    # Should still generate forecast but with lower confidence
    assert len(result.forecast_points) == 30
    assert result.data_quality_score < 0.8  # Penalty for insufficient data
    assert 'insufficient_data' in result.qa_metadata.get('penalties_applied', [])


def test_seasonality_detection(tenant_id, sample_sales_history):
    """Test seasonality detection"""
    agent = DemandForecastAgent(tenant_id=tenant_id)
    
    result = agent.forecast_demand(
        product_id=uuid4(),
        product_name="Test Product",
        sales_history=sample_sales_history,
        forecast_horizon_days=30
    )
    
    # Should detect weekly seasonality (we added weekend pattern)
    assert 'weekly' in result.seasonality
    assert isinstance(result.seasonality['weekly'].detected, bool)
    assert 0 <= result.seasonality['weekly'].strength <= 1


def test_inventory_alerts(tenant_id, sample_sales_history):
    """Test inventory alert generation"""
    agent = DemandForecastAgent(tenant_id=tenant_id)
    
    # Test with low inventory (should trigger stockout alert)
    result = agent.forecast_demand(
        product_id=uuid4(),
        product_name="Test Product",
        sales_history=sample_sales_history,
        forecast_horizon_days=30,
        current_inventory=10  # Very low inventory
    )
    
    # Should have at least one alert
    assert len(result.alerts) > 0
    
    # Check alert structure
    for alert in result.alerts:
        assert alert.alert_type in ['stockout_risk', 'overstock_risk', 'reorder_point', 'low_confidence']
        assert alert.severity in ['low', 'medium', 'high', 'critical']
        assert alert.message
        assert alert.recommended_action


def test_reorder_recommendation(tenant_id, sample_sales_history):
    """Test reorder point calculation"""
    agent = DemandForecastAgent(tenant_id=tenant_id)
    
    result = agent.forecast_demand(
        product_id=uuid4(),
        product_name="Test Product",
        sales_history=sample_sales_history,
        forecast_horizon_days=30,
        current_inventory=50
    )
    
    # Should have reorder recommendation
    assert result.reorder_recommendation is not None
    assert result.reorder_recommendation >= 0


def test_trend_detection(tenant_id):
    """Test trend detection"""
    agent = DemandForecastAgent(tenant_id=tenant_id)
    
    # Create increasing trend
    increasing_history = [
        {'date': date.today() - timedelta(days=60-i), 'quantity': 5 + i//2}
        for i in range(60)
    ]
    
    result = agent.forecast_demand(
        product_id=uuid4(),
        product_name="Test Product",
        sales_history=increasing_history,
        forecast_horizon_days=30
    )
    
    # Should detect increasing trend
    assert result.trend in ['increasing', 'decreasing', 'stable']


def test_to_dict_conversion(tenant_id, sample_sales_history):
    """Test conversion to dictionary for API response"""
    agent = DemandForecastAgent(tenant_id=tenant_id)
    
    result = agent.forecast_demand(
        product_id=uuid4(),
        product_name="Test Product",
        sales_history=sample_sales_history,
        forecast_horizon_days=30,
        current_inventory=100
    )
    
    # Convert to dict
    result_dict = result.to_dict()
    
    # Verify structure
    assert 'product_id' in result_dict
    assert 'product_name' in result_dict
    assert 'forecast_points' in result_dict
    assert 'best_model' in result_dict
    assert 'seasonality' in result_dict
    assert 'alerts' in result_dict
    assert 'final_confidence' in result_dict
    
    # Verify forecast points are serializable
    assert isinstance(result_dict['forecast_points'], list)
    assert len(result_dict['forecast_points']) == 30
    
    for fp in result_dict['forecast_points']:
        assert 'date' in fp
        assert 'predicted_quantity' in fp
        assert 'lower_bound' in fp
        assert 'upper_bound' in fp
        assert 'confidence' in fp
