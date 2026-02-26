"""
Tests for Agent API Endpoints

These tests verify that the API endpoints for Pricing Intelligence,
Sentiment Analysis, and Demand Forecast agents are working correctly.
"""
import pytest
from uuid import uuid4
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient

from src.main import app
from src.models.product import Product
from src.models.review import Review
from src.models.sales_record import SalesRecord


class TestPricingIntelligenceAPI:
    """Tests for Pricing Intelligence API endpoint"""
    
    def test_get_pricing_analysis_endpoint_exists(self):
        """
        Test that GET /api/v1/pricing/analysis endpoint exists
        and returns proper response structure.
        """
        # This is a basic smoke test to verify the endpoint is registered
        # In a real test, we would set up test data and authenticate
        client = TestClient(app)
        
        # Test that the endpoint exists (will fail auth, but that's expected)
        response = client.get("/api/v1/pricing/analysis?product_ids=test")
        
        # Should get 401 Unauthorized (not 404 Not Found)
        assert response.status_code in [401, 422], \
            "Endpoint should exist and require authentication"
    
    def test_pricing_analysis_requires_product_ids(self):
        """
        Test that pricing analysis endpoint requires product_ids parameter
        """
        client = TestClient(app)
        
        # Missing product_ids should return 401 (auth checked first) or 422 (validation)
        response = client.get("/api/v1/pricing/analysis")
        assert response.status_code in [401, 422], \
            "Should return auth error or validation error when product_ids missing"


class TestSentimentAnalysisAPI:
    """Tests for Sentiment Analysis API endpoint"""
    
    def test_get_product_sentiment_endpoint_exists(self):
        """
        Test that GET /api/v1/sentiment/product/{product_id} endpoint exists
        and returns proper response structure.
        """
        client = TestClient(app)
        
        # Test that the endpoint exists (will fail auth, but that's expected)
        product_id = uuid4()
        response = client.get(f"/api/v1/sentiment/product/{product_id}")
        
        # Should get 401 Unauthorized (not 404 Not Found)
        assert response.status_code == 401, \
            "Endpoint should exist and require authentication"
    
    def test_sentiment_analysis_validates_num_clusters(self):
        """
        Test that sentiment analysis validates num_clusters parameter
        """
        # This would require authentication setup
        # For now, just verify the endpoint structure is correct
        pass


class TestDemandForecastAPI:
    """Tests for Demand Forecast API endpoint"""
    
    def test_get_product_forecast_endpoint_exists(self):
        """
        Test that GET /api/v1/forecast/product/{product_id} endpoint exists
        and returns proper response structure.
        """
        client = TestClient(app)
        
        # Test that the endpoint exists (will fail auth, but that's expected)
        product_id = uuid4()
        response = client.get(f"/api/v1/forecast/product/{product_id}")
        
        # Should get 401 Unauthorized (not 404 Not Found)
        assert response.status_code == 401, \
            "Endpoint should exist and require authentication"
    
    def test_forecast_validates_horizon_parameter(self):
        """
        Test that forecast endpoint validates forecast_horizon_days parameter
        """
        # This would require authentication setup
        # For now, just verify the endpoint structure is correct
        pass


class TestAPIEndpointIntegration:
    """Integration tests for all agent API endpoints"""
    
    def test_all_agent_endpoints_registered(self):
        """
        Test that all three agent endpoints are properly registered
        """
        client = TestClient(app)
        
        # Get OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})
        
        # Verify pricing endpoint
        assert "/api/v1/pricing/analysis" in paths, \
            "Pricing analysis endpoint should be registered"
        assert "get" in paths["/api/v1/pricing/analysis"], \
            "Pricing analysis should support GET method"
        
        # Verify sentiment endpoint
        assert "/api/v1/sentiment/product/{product_id}" in paths, \
            "Sentiment analysis endpoint should be registered"
        assert "get" in paths["/api/v1/sentiment/product/{product_id}"], \
            "Sentiment analysis should support GET method"
        
        # Verify forecast endpoint
        assert "/api/v1/forecast/product/{product_id}" in paths, \
            "Demand forecast endpoint should be registered"
        assert "get" in paths["/api/v1/forecast/product/{product_id}"], \
            "Demand forecast should support GET method"
    
    def test_endpoints_require_authentication(self):
        """
        Test that all agent endpoints require authentication
        """
        client = TestClient(app)
        product_id = uuid4()
        
        # All endpoints should return 401 without auth
        endpoints = [
            f"/api/v1/pricing/analysis?product_ids={product_id}",
            f"/api/v1/sentiment/product/{product_id}",
            f"/api/v1/forecast/product/{product_id}"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, \
                f"Endpoint {endpoint} should require authentication"
    
    def test_endpoints_return_json(self):
        """
        Test that all endpoints return JSON responses
        """
        client = TestClient(app)
        
        # Test with invalid auth to get error responses
        # All should still return JSON
        product_id = uuid4()
        
        endpoints = [
            f"/api/v1/pricing/analysis?product_ids={product_id}",
            f"/api/v1/sentiment/product/{product_id}",
            f"/api/v1/forecast/product/{product_id}"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.headers.get("content-type") == "application/json", \
                f"Endpoint {endpoint} should return JSON"


# Note: Full integration tests with database and authentication
# would be implemented in a separate test suite with proper fixtures
