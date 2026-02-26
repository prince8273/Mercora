"""
Demand Forecast Agent - Time Series Forecasting for Inventory Intelligence

This agent provides demand forecasting using multiple models:
- ARIMA: Classical statistical approach
- Prophet: Facebook's robust forecasting library
- Exponential Smoothing: Simple but effective baseline
- Moving Average: Quick baseline for comparison

The agent follows the tiered intelligence architecture with QA-adjusted confidence.
"""
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from decimal import Decimal
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from dataclasses import dataclass

# Statistical models
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose

# Prophet (optional - graceful fallback if not installed)
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("Warning: Prophet not installed. Install with: pip install prophet")


@dataclass
class ForecastPoint:
    """Single forecast data point"""
    date: date
    predicted_quantity: float
    lower_bound: float
    upper_bound: float
    confidence: float


@dataclass
class SeasonalityPattern:
    """Detected seasonality pattern"""
    period: str  # 'daily', 'weekly', 'monthly', 'yearly'
    strength: float  # 0-1
    detected: bool


@dataclass
class InventoryAlert:
    """Inventory risk alert"""
    alert_type: str  # 'stockout_risk', 'overstock_risk', 'reorder_point'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    recommended_action: str
    days_until_event: Optional[int]


@dataclass
class ModelPerformance:
    """Performance metrics for a forecasting model"""
    model_name: str
    mae: float  # Mean Absolute Error
    rmse: float  # Root Mean Squared Error
    mape: float  # Mean Absolute Percentage Error
    confidence_score: float  # 0-1


@dataclass
class DemandForecastResult:
    """Complete demand forecast result with QA-adjusted confidence"""
    product_id: UUID
    product_name: str
    forecast_horizon_days: int
    forecast_points: List[ForecastPoint]
    
    # Model comparison
    best_model: str
    model_performances: List[ModelPerformance]
    
    # Seasonality analysis
    seasonality: Dict[str, SeasonalityPattern]
    trend: str  # 'increasing', 'decreasing', 'stable'
    
    # Inventory intelligence
    current_inventory: Optional[int]
    alerts: List[InventoryAlert]
    reorder_recommendation: Optional[int]
    
    # Confidence and QA
    base_confidence: float
    data_quality_score: float
    final_confidence: float
    qa_metadata: Dict
    
    # Metadata
    historical_data_points: int
    forecast_generated_at: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            "product_id": str(self.product_id),
            "product_name": self.product_name,
            "forecast_horizon_days": self.forecast_horizon_days,
            "forecast_points": [
                {
                    "date": fp.date.isoformat(),
                    "predicted_quantity": round(fp.predicted_quantity, 2),
                    "lower_bound": round(fp.lower_bound, 2),
                    "upper_bound": round(fp.upper_bound, 2),
                    "confidence": round(fp.confidence, 3)
                }
                for fp in self.forecast_points
            ],
            "best_model": self.best_model,
            "model_performances": [
                {
                    "model_name": mp.model_name,
                    "mae": round(mp.mae, 2),
                    "rmse": round(mp.rmse, 2),
                    "mape": round(mp.mape, 2),
                    "confidence_score": round(mp.confidence_score, 3)
                }
                for mp in self.model_performances
            ],
            "seasonality": {
                period: {
                    "detected": pattern.detected,
                    "strength": round(pattern.strength, 3)
                }
                for period, pattern in self.seasonality.items()
            },
            "trend": self.trend,
            "current_inventory": self.current_inventory,
            "alerts": [
                {
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "recommended_action": alert.recommended_action,
                    "days_until_event": alert.days_until_event
                }
                for alert in self.alerts
            ],
            "reorder_recommendation": self.reorder_recommendation,
            "base_confidence": round(self.base_confidence, 3),
            "data_quality_score": round(self.data_quality_score, 3),
            "final_confidence": round(self.final_confidence, 3),
            "qa_metadata": self.qa_metadata,
            "historical_data_points": self.historical_data_points,
            "forecast_generated_at": self.forecast_generated_at.isoformat()
        }


class DemandForecastAgent:
    """
    Demand Forecast Agent - Multi-model time series forecasting
    
    Features:
    - Multiple forecasting models (ARIMA, Prophet, Exponential Smoothing)
    - Automatic model selection based on performance
    - Seasonality detection and decomposition
    - Inventory risk alerts
    - QA-adjusted confidence scoring
    """
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize Demand Forecast Agent
        
        Args:
            tenant_id: Tenant UUID for multi-tenancy isolation
        """
        self.tenant_id = tenant_id
        self.min_data_points = 14  # Minimum 2 weeks of data
        self.confidence_threshold = 0.6
    
    def forecast_demand(
        self,
        product_id: UUID,
        product_name: str,
        sales_history: List[Dict],
        forecast_horizon_days: int = 30,
        current_inventory: Optional[int] = None
    ) -> DemandForecastResult:
        """
        Generate demand forecast for a product
        
        Args:
            product_id: Product UUID
            product_name: Product name
            sales_history: List of sales records with 'date' and 'quantity'
            forecast_horizon_days: Number of days to forecast (default: 30)
            current_inventory: Current inventory level (optional)
        
        Returns:
            DemandForecastResult with forecasts and confidence
        """
        # Convert to DataFrame
        df = self._prepare_data(sales_history)
        
        # Check data quality
        data_quality_score, qa_metadata = self._assess_data_quality(df, forecast_horizon_days)
        
        # Detect seasonality
        seasonality = self._detect_seasonality(df)
        trend = self._detect_trend(df)
        
        # Generate forecasts with multiple models
        model_results = self._generate_multi_model_forecasts(df, forecast_horizon_days)
        
        # Select best model
        best_model_name, best_forecast, model_performances = self._select_best_model(
            model_results, df
        )
        
        # Calculate base confidence
        base_confidence = self._calculate_base_confidence(
            df, best_forecast, model_performances
        )
        
        # Apply QA adjustment
        final_confidence = base_confidence * data_quality_score
        
        # Generate inventory alerts
        alerts = self._generate_inventory_alerts(
            df, best_forecast, current_inventory, final_confidence
        )
        
        # Calculate reorder recommendation
        reorder_recommendation = self._calculate_reorder_point(
            best_forecast, current_inventory
        )
        
        return DemandForecastResult(
            product_id=product_id,
            product_name=product_name,
            forecast_horizon_days=forecast_horizon_days,
            forecast_points=best_forecast,
            best_model=best_model_name,
            model_performances=model_performances,
            seasonality=seasonality,
            trend=trend,
            current_inventory=current_inventory,
            alerts=alerts,
            reorder_recommendation=reorder_recommendation,
            base_confidence=base_confidence,
            data_quality_score=data_quality_score,
            final_confidence=final_confidence,
            qa_metadata=qa_metadata,
            historical_data_points=len(df),
            forecast_generated_at=datetime.utcnow()
        )
    
    def _prepare_data(self, sales_history: List[Dict]) -> pd.DataFrame:
        """Prepare sales data for forecasting"""
        df = pd.DataFrame(sales_history)
        
        # Convert date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        else:
            raise ValueError("Sales history must contain 'date' column")
        
        # Ensure quantity column
        if 'quantity' not in df.columns:
            raise ValueError("Sales history must contain 'quantity' column")
        
        # Sort by date
        df = df.sort_values('date')
        
        # Aggregate by date (in case of multiple records per day)
        df = df.groupby('date')['quantity'].sum().reset_index()
        
        # Fill missing dates with 0
        date_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
        df = df.set_index('date').reindex(date_range, fill_value=0).reset_index()
        df.columns = ['date', 'quantity']
        
        return df
    
    def _assess_data_quality(
        self, df: pd.DataFrame, forecast_horizon: int
    ) -> Tuple[float, Dict]:
        """Assess data quality for forecasting"""
        qa_metadata = {}
        penalties = []
        
        # Check 1: Sufficient data points
        data_points = len(df)
        qa_metadata['data_points'] = data_points
        
        if data_points < self.min_data_points:
            penalties.append(('insufficient_data', 0.5))
            qa_metadata['insufficient_data'] = True
        elif data_points < forecast_horizon * 2:
            penalties.append(('limited_data', 0.2))
            qa_metadata['limited_data'] = True
        
        # Check 2: Data recency
        days_since_last_sale = (datetime.now().date() - df['date'].max().date()).days
        qa_metadata['days_since_last_sale'] = days_since_last_sale
        
        if days_since_last_sale > 7:
            penalties.append(('stale_data', 0.15))
            qa_metadata['stale_data'] = True
        
        # Check 3: Zero sales ratio
        zero_ratio = (df['quantity'] == 0).sum() / len(df)
        qa_metadata['zero_sales_ratio'] = round(zero_ratio, 3)
        
        if zero_ratio > 0.5:
            penalties.append(('high_zero_ratio', 0.25))
            qa_metadata['high_zero_ratio'] = True
        elif zero_ratio > 0.3:
            penalties.append(('moderate_zero_ratio', 0.1))
        
        # Check 4: Variance (too stable or too volatile)
        if df['quantity'].std() == 0:
            penalties.append(('no_variance', 0.3))
            qa_metadata['no_variance'] = True
        else:
            cv = df['quantity'].std() / (df['quantity'].mean() + 1)  # Coefficient of variation
            qa_metadata['coefficient_of_variation'] = round(cv, 3)
            
            if cv > 0.8:  # Lowered from 2.0 to 0.8 for better volatility detection
                penalties.append(('high_volatility', 0.15))
                qa_metadata['high_volatility'] = True
        
        # Calculate quality score
        quality_score = 1.0
        for reason, penalty in penalties:
            quality_score *= (1 - penalty)
        
        qa_metadata['quality_score'] = round(quality_score, 3)
        qa_metadata['penalties_applied'] = [reason for reason, _ in penalties]
        
        return quality_score, qa_metadata
    
    def _detect_seasonality(self, df: pd.DataFrame) -> Dict[str, SeasonalityPattern]:
        """Detect seasonal patterns in the data"""
        seasonality = {}
        
        if len(df) < 14:
            # Not enough data for seasonality detection
            return {
                'weekly': SeasonalityPattern('weekly', 0.0, False),
                'monthly': SeasonalityPattern('monthly', 0.0, False)
            }
        
        try:
            # Weekly seasonality (7 days)
            if len(df) >= 14:
                decomposition = seasonal_decompose(
                    df['quantity'], model='additive', period=7, extrapolate_trend='freq'
                )
                seasonal_strength = np.std(decomposition.seasonal) / (np.std(df['quantity']) + 1e-10)
                seasonality['weekly'] = SeasonalityPattern(
                    'weekly',
                    min(seasonal_strength, 1.0),
                    bool(seasonal_strength > 0.1)  # Convert numpy bool to Python bool
                )
            
            # Monthly seasonality (30 days)
            if len(df) >= 60:
                decomposition = seasonal_decompose(
                    df['quantity'], model='additive', period=30, extrapolate_trend='freq'
                )
                seasonal_strength = np.std(decomposition.seasonal) / (np.std(df['quantity']) + 1e-10)
                seasonality['monthly'] = SeasonalityPattern(
                    'monthly',
                    min(seasonal_strength, 1.0),
                    bool(seasonal_strength > 0.1)  # Convert numpy bool to Python bool
                )
            else:
                seasonality['monthly'] = SeasonalityPattern('monthly', 0.0, False)
        
        except Exception as e:
            # Fallback if decomposition fails
            seasonality['weekly'] = SeasonalityPattern('weekly', 0.0, False)
            seasonality['monthly'] = SeasonalityPattern('monthly', 0.0, False)
        
        return seasonality
    
    def _detect_trend(self, df: pd.DataFrame) -> str:
        """Detect overall trend in the data"""
        if len(df) < 7:
            return 'stable'
        
        # Simple linear regression on recent data
        recent_data = df.tail(30)
        x = np.arange(len(recent_data))
        y = recent_data['quantity'].values
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        # Determine trend
        mean_quantity = df['quantity'].mean()
        if abs(slope) < mean_quantity * 0.01:  # Less than 1% change per day
            return 'stable'
        elif slope > 0:
            return 'increasing'
        else:
            return 'decreasing'
    
    def _generate_multi_model_forecasts(
        self, df: pd.DataFrame, horizon: int
    ) -> Dict[str, List[ForecastPoint]]:
        """Generate forecasts using multiple models"""
        results = {}
        
        # Model 1: Moving Average (baseline)
        results['moving_average'] = self._forecast_moving_average(df, horizon)
        
        # Model 2: Exponential Smoothing
        results['exponential_smoothing'] = self._forecast_exponential_smoothing(df, horizon)
        
        # Model 3: ARIMA
        results['arima'] = self._forecast_arima(df, horizon)
        
        # Model 4: Prophet (if available)
        if PROPHET_AVAILABLE:
            results['prophet'] = self._forecast_prophet(df, horizon)
        
        return results
    
    def _forecast_moving_average(
        self, df: pd.DataFrame, horizon: int
    ) -> List[ForecastPoint]:
        """Simple moving average forecast"""
        window = min(7, len(df))
        ma = df['quantity'].rolling(window=window).mean().iloc[-1]
        
        forecast_points = []
        last_date = df['date'].max()
        
        for i in range(1, horizon + 1):
            forecast_date = (last_date + timedelta(days=i)).date()
            # Simple forecast with increasing uncertainty
            uncertainty = ma * 0.2 * (i / horizon)
            
            forecast_points.append(ForecastPoint(
                date=forecast_date,
                predicted_quantity=max(0, ma),
                lower_bound=max(0, ma - uncertainty),
                upper_bound=ma + uncertainty,
                confidence=max(0.3, 1.0 - (i / horizon) * 0.5)
            ))
        
        return forecast_points
    
    def _forecast_exponential_smoothing(
        self, df: pd.DataFrame, horizon: int
    ) -> List[ForecastPoint]:
        """Exponential smoothing forecast"""
        try:
            model = ExponentialSmoothing(
                df['quantity'],
                seasonal_periods=7 if len(df) >= 14 else None,
                trend='add' if len(df) >= 14 else None,
                seasonal='add' if len(df) >= 14 else None
            )
            fitted_model = model.fit()
            forecast = fitted_model.forecast(steps=horizon)
            
            forecast_points = []
            last_date = df['date'].max()
            
            for i, value in enumerate(forecast, 1):
                forecast_date = (last_date + timedelta(days=i)).date()
                uncertainty = abs(value) * 0.15 * (i / horizon)
                
                forecast_points.append(ForecastPoint(
                    date=forecast_date,
                    predicted_quantity=max(0, value),
                    lower_bound=max(0, value - uncertainty),
                    upper_bound=value + uncertainty,
                    confidence=max(0.4, 1.0 - (i / horizon) * 0.4)
                ))
            
            return forecast_points
        
        except Exception:
            # Fallback to moving average
            return self._forecast_moving_average(df, horizon)
    
    def _forecast_arima(
        self, df: pd.DataFrame, horizon: int
    ) -> List[ForecastPoint]:
        """ARIMA forecast"""
        try:
            # Auto-select ARIMA parameters (simplified)
            model = ARIMA(df['quantity'], order=(1, 1, 1))
            fitted_model = model.fit()
            forecast_result = fitted_model.forecast(steps=horizon)
            
            forecast_points = []
            last_date = df['date'].max()
            
            for i, value in enumerate(forecast_result, 1):
                forecast_date = (last_date + timedelta(days=i)).date()
                uncertainty = abs(value) * 0.2 * (i / horizon)
                
                forecast_points.append(ForecastPoint(
                    date=forecast_date,
                    predicted_quantity=max(0, value),
                    lower_bound=max(0, value - uncertainty),
                    upper_bound=value + uncertainty,
                    confidence=max(0.5, 1.0 - (i / horizon) * 0.3)
                ))
            
            return forecast_points
        
        except Exception:
            # Fallback to exponential smoothing
            return self._forecast_exponential_smoothing(df, horizon)
    
    def _forecast_prophet(
        self, df: pd.DataFrame, horizon: int
    ) -> List[ForecastPoint]:
        """Prophet forecast (Facebook's forecasting library)"""
        try:
            # Prepare data for Prophet
            prophet_df = df.rename(columns={'date': 'ds', 'quantity': 'y'})
            
            # Initialize and fit model
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True if len(df) >= 14 else False,
                yearly_seasonality=False
            )
            model.fit(prophet_df)
            
            # Generate future dates
            future = model.make_future_dataframe(periods=horizon)
            forecast = model.predict(future)
            
            # Extract forecast points
            forecast_points = []
            forecast_data = forecast.tail(horizon)
            
            for _, row in forecast_data.iterrows():
                forecast_points.append(ForecastPoint(
                    date=row['ds'].date(),
                    predicted_quantity=max(0, row['yhat']),
                    lower_bound=max(0, row['yhat_lower']),
                    upper_bound=max(0, row['yhat_upper']),
                    confidence=0.7  # Prophet provides good confidence
                ))
            
            return forecast_points
        
        except Exception:
            # Fallback to ARIMA
            return self._forecast_arima(df, horizon)
    
    def _select_best_model(
        self, model_results: Dict[str, List[ForecastPoint]], df: pd.DataFrame
    ) -> Tuple[str, List[ForecastPoint], List[ModelPerformance]]:
        """Select best model based on historical performance"""
        if len(df) < 14:
            # Not enough data for validation, use exponential smoothing
            return 'exponential_smoothing', model_results['exponential_smoothing'], []
        
        # Use last 7 days as validation set
        train_df = df.iloc[:-7]
        test_df = df.iloc[-7:]
        
        performances = []
        
        for model_name, _ in model_results.items():
            try:
                # Generate forecast for validation period
                if model_name == 'moving_average':
                    val_forecast = self._forecast_moving_average(train_df, 7)
                elif model_name == 'exponential_smoothing':
                    val_forecast = self._forecast_exponential_smoothing(train_df, 7)
                elif model_name == 'arima':
                    val_forecast = self._forecast_arima(train_df, 7)
                elif model_name == 'prophet':
                    val_forecast = self._forecast_prophet(train_df, 7)
                else:
                    continue
                
                # Calculate errors
                predictions = [fp.predicted_quantity for fp in val_forecast]
                actuals = test_df['quantity'].values
                
                mae = np.mean(np.abs(predictions - actuals))
                rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
                mape = np.mean(np.abs((actuals - predictions) / (actuals + 1))) * 100
                
                # Convert to confidence score (lower error = higher confidence)
                confidence = 1.0 / (1.0 + mae / (np.mean(actuals) + 1))
                
                performances.append(ModelPerformance(
                    model_name=model_name,
                    mae=mae,
                    rmse=rmse,
                    mape=mape,
                    confidence_score=confidence
                ))
            
            except Exception:
                continue
        
        # Select best model (highest confidence)
        if performances:
            best_performance = max(performances, key=lambda p: p.confidence_score)
            best_model_name = best_performance.model_name
        else:
            # Default to exponential smoothing
            best_model_name = 'exponential_smoothing'
        
        return best_model_name, model_results[best_model_name], performances
    
    def _calculate_base_confidence(
        self,
        df: pd.DataFrame,
        forecast: List[ForecastPoint],
        performances: List[ModelPerformance]
    ) -> float:
        """Calculate base confidence before QA adjustment"""
        confidence_factors = []
        
        # Factor 1: Data quantity
        data_factor = min(1.0, len(df) / 60)  # Full confidence at 60+ days
        confidence_factors.append(data_factor)
        
        # Factor 2: Model performance
        if performances:
            best_performance = max(performances, key=lambda p: p.confidence_score)
            confidence_factors.append(best_performance.confidence_score)
        else:
            confidence_factors.append(0.6)
        
        # Factor 3: Forecast stability (variance in predictions)
        predictions = [fp.predicted_quantity for fp in forecast]
        if np.std(predictions) > 0:
            stability = 1.0 / (1.0 + np.std(predictions) / (np.mean(predictions) + 1))
            confidence_factors.append(stability)
        
        # Combine factors (geometric mean)
        base_confidence = np.prod(confidence_factors) ** (1 / len(confidence_factors))
        
        return float(base_confidence)
    
    def _generate_inventory_alerts(
        self,
        df: pd.DataFrame,
        forecast: List[ForecastPoint],
        current_inventory: Optional[int],
        confidence: float
    ) -> List[InventoryAlert]:
        """Generate inventory risk alerts"""
        alerts = []
        
        if current_inventory is None:
            return alerts
        
        # Calculate average daily demand from forecast
        avg_daily_demand = np.mean([fp.predicted_quantity for fp in forecast[:7]])
        
        # Alert 1: Stockout risk
        days_of_stock = current_inventory / (avg_daily_demand + 1)
        
        if days_of_stock < 3:
            alerts.append(InventoryAlert(
                alert_type='stockout_risk',
                severity='critical',
                message=f'Critical stockout risk: Only {days_of_stock:.1f} days of inventory remaining',
                recommended_action='Place emergency order immediately',
                days_until_event=int(days_of_stock)
            ))
        elif days_of_stock < 7:
            alerts.append(InventoryAlert(
                alert_type='stockout_risk',
                severity='high',
                message=f'High stockout risk: {days_of_stock:.1f} days of inventory remaining',
                recommended_action='Place order within 24 hours',
                days_until_event=int(days_of_stock)
            ))
        elif days_of_stock < 14:
            alerts.append(InventoryAlert(
                alert_type='reorder_point',
                severity='medium',
                message=f'Approaching reorder point: {days_of_stock:.1f} days of inventory',
                recommended_action='Review and place order soon',
                days_until_event=int(days_of_stock)
            ))
        
        # Alert 2: Overstock risk
        if days_of_stock > 90:
            alerts.append(InventoryAlert(
                alert_type='overstock_risk',
                severity='medium',
                message=f'Overstock detected: {days_of_stock:.1f} days of inventory',
                recommended_action='Consider promotional pricing or reduce future orders',
                days_until_event=None
            ))
        
        # Alert 3: Low confidence warning
        if confidence < self.confidence_threshold:
            alerts.append(InventoryAlert(
                alert_type='low_confidence',
                severity='low',
                message=f'Forecast confidence is low ({confidence:.2f})',
                recommended_action='Collect more sales data or use safety stock',
                days_until_event=None
            ))
        
        return alerts
    
    def _calculate_reorder_point(
        self,
        forecast: List[ForecastPoint],
        current_inventory: Optional[int]
    ) -> Optional[int]:
        """Calculate recommended reorder quantity"""
        if current_inventory is None:
            return None
        
        # Calculate expected demand for next 30 days
        expected_demand_30d = sum(fp.predicted_quantity for fp in forecast[:30])
        
        # Safety stock (20% buffer)
        safety_stock = expected_demand_30d * 0.2
        
        # Reorder point: expected demand + safety stock - current inventory
        reorder_quantity = int(expected_demand_30d + safety_stock - current_inventory)
        
        return max(0, reorder_quantity)
