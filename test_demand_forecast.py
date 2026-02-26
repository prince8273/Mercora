"""Test script for Demand Forecast Agent"""
import asyncio
from datetime import date, timedelta
from uuid import uuid4
from src.agents.demand_forecast_agent import DemandForecastAgent


def generate_sample_sales_data(days=60, base_quantity=100, trend=0.5, seasonality=True):
    """Generate sample sales data with trend and seasonality"""
    sales_history = []
    start_date = date.today() - timedelta(days=days)
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # Base quantity with trend
        quantity = base_quantity + (trend * i)
        
        # Add weekly seasonality (higher on weekends)
        if seasonality and current_date.weekday() in [5, 6]:  # Saturday, Sunday
            quantity *= 1.3
        
        # Add some randomness
        import random
        quantity *= random.uniform(0.8, 1.2)
        
        sales_history.append({
            'date': current_date.isoformat(),
            'quantity': int(quantity)
        })
    
    return sales_history


async def main():
    """Test the Demand Forecast Agent"""
    print("\n" + "="*80)
    print("DEMAND FORECAST AGENT TEST")
    print("="*80)
    
    # Initialize agent
    tenant_id = uuid4()
    agent = DemandForecastAgent(tenant_id=tenant_id)
    print(f"\n✓ Agent initialized for tenant: {tenant_id}")
    
    # Test 1: Basic forecast with trend and seasonality
    print("\n" + "-"*80)
    print("TEST 1: Forecast with trend and seasonality")
    print("-"*80)
    
    sales_history = generate_sample_sales_data(days=60, base_quantity=100, trend=0.5, seasonality=True)
    
    result = agent.forecast_demand(
        product_id=uuid4(),
        product_name="Test Product - Trending",
        sales_history=sales_history,
        forecast_horizon_days=30,
        current_inventory=500
    )
    
    print(f"\n✓ Forecast generated successfully!")
    print(f"  - Product: {result.product_name}")
    print(f"  - Historical data points: {result.historical_data_points}")
    print(f"  - Forecast horizon: {result.forecast_horizon_days} days")
    print(f"  - Best model: {result.best_model}")
    print(f"  - Trend: {result.trend}")
    print(f"  - Data quality score: {result.data_quality_score:.3f}")
    print(f"  - Final confidence: {result.final_confidence:.3f}")
    
    # Show seasonality detection
    print(f"\n  Seasonality detected:")
    for period, pattern in result.seasonality.items():
        status = "✓ Yes" if pattern.detected else "✗ No"
        print(f"    - {period.capitalize()}: {status} (strength: {pattern.strength:.3f})")
    
    # Show model performances
    print(f"\n  Model performances:")
    for perf in result.model_performances:
        print(f"    - {perf.model_name}: MAE={perf.mae:.2f}, RMSE={perf.rmse:.2f}, Confidence={perf.confidence_score:.3f}")
    
    # Show first 7 days of forecast
    print(f"\n  First 7 days forecast:")
    for fp in result.forecast_points[:7]:
        print(f"    - {fp.date}: {fp.predicted_quantity:.1f} units (confidence: {fp.confidence:.3f})")
    
    # Show alerts
    if result.alerts:
        print(f"\n  Alerts ({len(result.alerts)}):")
        for alert in result.alerts:
            print(f"    - [{alert.severity.upper()}] {alert.message}")
            print(f"      Action: {alert.recommended_action}")
    
    # Show reorder recommendation
    if result.reorder_recommendation:
        print(f"\n  Reorder recommendation: {result.reorder_recommendation} units")
    
    # Test 2: Low data quality scenario
    print("\n" + "-"*80)
    print("TEST 2: Low data quality (insufficient data)")
    print("-"*80)
    
    limited_sales = generate_sample_sales_data(days=10, base_quantity=50, trend=0, seasonality=False)
    
    result2 = agent.forecast_demand(
        product_id=uuid4(),
        product_name="Test Product - Limited Data",
        sales_history=limited_sales,
        forecast_horizon_days=30,
        current_inventory=100
    )
    
    print(f"\n✓ Forecast generated with limited data")
    print(f"  - Historical data points: {result2.historical_data_points}")
    print(f"  - Data quality score: {result2.data_quality_score:.3f}")
    print(f"  - Final confidence: {result2.final_confidence:.3f}")
    print(f"  - QA penalties: {result2.qa_metadata.get('penalties_applied', [])}")
    
    # Test 3: Check Prophet availability
    print("\n" + "-"*80)
    print("TEST 3: Prophet availability check")
    print("-"*80)
    
    from src.agents.demand_forecast_agent import PROPHET_AVAILABLE
    if PROPHET_AVAILABLE:
        print("✓ Prophet is installed and available")
    else:
        print("✗ Prophet is NOT available")
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
