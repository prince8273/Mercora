"""Schemas for demand forecasting"""
from datetime import date, datetime
from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ForecastPointSchema(BaseModel):
    """Single forecast data point"""
    date: date
    predicted_quantity: float
    lower_bound: float
    upper_bound: float
    confidence: float


class SeasonalityPatternSchema(BaseModel):
    """Seasonality pattern"""
    detected: bool
    strength: float


class InventoryAlertSchema(BaseModel):
    """Inventory alert"""
    alert_type: str
    severity: str
    message: str
    recommended_action: str
    days_until_event: Optional[int]


class ModelPerformanceSchema(BaseModel):
    """Model performance metrics"""
    model_name: str
    mae: float
    rmse: float
    mape: float
    confidence_score: float


class DemandForecastResponse(BaseModel):
    """Demand forecast response"""
    product_id: UUID
    product_name: str
    forecast_horizon_days: int
    forecast_points: List[ForecastPointSchema]
    
    best_model: str
    model_performances: List[ModelPerformanceSchema]
    
    seasonality: Dict[str, SeasonalityPatternSchema]
    trend: str
    
    current_inventory: Optional[int]
    alerts: List[InventoryAlertSchema]
    reorder_recommendation: Optional[int]
    
    base_confidence: float
    data_quality_score: float
    final_confidence: float
    qa_metadata: Dict
    
    historical_data_points: int
    forecast_generated_at: datetime
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "550e8400-e29b-41d4-a716-446655440000",
                "product_name": "Wireless Mouse",
                "forecast_horizon_days": 30,
                "forecast_points": [
                    {
                        "date": "2026-02-21",
                        "predicted_quantity": 45.2,
                        "lower_bound": 38.5,
                        "upper_bound": 52.0,
                        "confidence": 0.85
                    }
                ],
                "best_model": "prophet",
                "model_performances": [
                    {
                        "model_name": "prophet",
                        "mae": 3.2,
                        "rmse": 4.5,
                        "mape": 8.5,
                        "confidence_score": 0.88
                    }
                ],
                "seasonality": {
                    "weekly": {"detected": True, "strength": 0.65},
                    "monthly": {"detected": False, "strength": 0.12}
                },
                "trend": "increasing",
                "current_inventory": 150,
                "alerts": [
                    {
                        "alert_type": "reorder_point",
                        "severity": "medium",
                        "message": "Approaching reorder point: 12.5 days of inventory",
                        "recommended_action": "Review and place order soon",
                        "days_until_event": 12
                    }
                ],
                "reorder_recommendation": 500,
                "base_confidence": 0.82,
                "data_quality_score": 0.95,
                "final_confidence": 0.78,
                "qa_metadata": {
                    "data_points": 60,
                    "zero_sales_ratio": 0.15,
                    "coefficient_of_variation": 0.45
                },
                "historical_data_points": 60,
                "forecast_generated_at": "2026-02-20T10:30:00"
            }
        }
    )


class ForecastRequest(BaseModel):
    """Request for demand forecast"""
    product_id: UUID = Field(..., description="Product UUID")
    forecast_horizon_days: int = Field(30, ge=7, le=90, description="Forecast horizon (7-90 days)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "550e8400-e29b-41d4-a716-446655440000",
                "forecast_horizon_days": 30
            }
        }
    )
