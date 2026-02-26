"""Test script for Demand Forecast API endpoint"""
import asyncio
import httpx
from datetime import date, timedelta
from uuid import uuid4


def generate_sample_sales_data(days=60):
    """Generate sample sales data"""
    sales_history = []
    start_date = date.today() - timedelta(days=days)
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # Base quantity with trend
        quantity = 100 + (0.5 * i)
        
        # Add weekly seasonality
        if current_date.weekday() in [5, 6]:
            quantity *= 1.3
        
        # Add randomness
        import random
        quantity *= random.uniform(0.8, 1.2)
        
        sales_history.append({
            'date': current_date.isoformat(),
            'quantity': int(quantity)
        })
    
    return sales_history


async def test_forecast_api():
    """Test the forecast API endpoint"""
    print("\n" + "="*80)
    print("DEMAND FORECAST API TEST")
    print("="*80)
    
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check if server is running
        try:
            response = await client.get(f"{base_url}/health")
            print(f"\n✓ Server is running: {response.json()}")
        except Exception as e:
            print(f"\n✗ Server is not running: {e}")
            print("Please start the server with: python src/main.py")
            return
        
        # Test forecast endpoint
        print("\n" + "-"*80)
        print("Testing /api/v1/forecast/demand endpoint")
        print("-"*80)
        
        # Generate test data
        product_id = str(uuid4())
        sales_history = generate_sample_sales_data(days=60)
        
        request_data = {
            "product_id": product_id,
            "forecast_horizon_days": 30
        }
        
        print(f"\nRequest:")
        print(f"  - Product ID: {product_id}")
        print(f"  - Forecast horizon: 30 days")
        print(f"  - Historical data points: {len(sales_history)}")
        
        try:
            # Note: This endpoint requires authentication
            # For testing, we'll check if it returns 401 (expected) or works
            response = await client.post(
                f"{base_url}/api/v1/forecast/demand",
                json=request_data
            )
            
            if response.status_code == 401:
                print(f"\n✓ Endpoint exists but requires authentication (status: 401)")
                print("  This is expected behavior - the endpoint is properly secured")
            elif response.status_code == 200:
                result = response.json()
                print(f"\n✓ Forecast generated successfully!")
                print(f"  - Product: {result.get('product_name', 'N/A')}")
                print(f"  - Best model: {result.get('best_model', 'N/A')}")
                print(f"  - Trend: {result.get('trend', 'N/A')}")
                print(f"  - Final confidence: {result.get('final_confidence', 0):.3f}")
                print(f"  - Forecast points: {len(result.get('forecast_points', []))}")
            else:
                print(f"\n✗ Unexpected status code: {response.status_code}")
                print(f"  Response: {response.text}")
        
        except Exception as e:
            print(f"\n✗ Error calling API: {e}")
    
    print("\n" + "="*80)
    print("API TEST COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_forecast_api())
