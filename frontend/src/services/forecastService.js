/**
 * Forecast Service
 * Handles all demand forecasting-related API calls
 */

import { apiClient } from '../lib/apiClient'

const HORIZON_MAP = { '7d': 7, '30d': 30, '60d': 60, '90d': 90 }

// Map severity -> priority label the components expect
const SEVERITY_TO_PRIORITY = { critical: 'critical', high: 'critical', medium: 'warning', low: 'info', info: 'info' }

/**
 * Transform raw API forecast response into the shape the components expect.
 * API returns: forecast_points[], alerts[]{severity, recommended_action, alert_type, message}
 * Components expect: { historical[], forecast[], stats{}, alerts[]{priority, title, recommendation, message} }
 */
function transformForecastResponse(response) {
  const points = response.forecast_points || []

  // Historical sales for the actual line
  const historical = (response.historical_sales || []).map((p) => ({
    date: p.date?.slice(0, 10),
    actual: p.quantity,
    type: 'historical',
  }))

  // Future forecast points
  const forecast = points.map((p) => ({
    date: p.date?.slice(0, 10),
    predicted: p.predicted_quantity,
    confidenceLower: p.lower_bound,
    confidenceUpper: p.upper_bound,
    confidence: p.confidence,
    type: 'forecast',
  }))

  // Build stats
  const quantities = points.map((p) => p.predicted_quantity).filter((q) => q != null)
  const avgForecast = quantities.length ? quantities.reduce((a, b) => a + b, 0) / quantities.length : 0
  const peakDemand = quantities.length ? Math.max(...quantities) : 0

  const histQty = (response.historical_sales || []).map((p) => p.quantity).filter((q) => q != null)
  const avgHistorical = histQty.length ? histQty.reduce((a, b) => a + b, 0) / histQty.length : null

  const stats = {
    avgHistorical: avgHistorical != null ? parseFloat(avgHistorical.toFixed(1)) : null,
    avgForecast: quantities.length ? parseFloat(avgForecast.toFixed(1)) : null,
    peakDemand: quantities.length ? parseFloat(peakDemand.toFixed(1)) : null,
    change: avgHistorical ? parseFloat((((avgForecast - avgHistorical) / avgHistorical) * 100).toFixed(1)) : null,
    confidence: response.final_confidence != null ? Math.round(response.final_confidence * 100) : null,
  }

  // Map alerts to component shape
  const alerts = (response.alerts || []).map((a, i) => ({
    id: `alert-${i}`,
    priority: SEVERITY_TO_PRIORITY[a.severity] || 'info',
    title: a.alert_type?.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) || 'Alert',
    message: a.message,
    recommendation: a.recommended_action,
    productName: response.product_name,
    createdAt: response.forecast_generated_at,
    actionable: !!a.recommended_action,
  }))

  return {
    historical,
    forecast,
    stats,
    alerts,
    gapAnalysis: response.reorder_recommendation ? {
      supplyGap: response.reorder_recommendation,
      currentInventory: response.current_inventory,
    } : null,
    accuracy: {
      mape: response.model_performances?.[0]?.mape ?? null,
      rmse: response.model_performances?.[0]?.rmse ?? null,
      confidence: response.final_confidence ?? null,
    },
    raw: response,
  }
}

export const forecastService = {
  async getDemandForecast(productId, options = {}) {
    const horizon = options?.horizon || options || '30d'
    const days = HORIZON_MAP[horizon] || 30
    try {
      const response = await apiClient.get(`/api/v1/forecast/product/${productId}`, {
        params: { forecast_horizon_days: days },
      })
      return transformForecastResponse(response)
    } catch {
      // Product has no sales history or other error — return empty shape so chart shows proper message
      return { historical: [], forecast: [], stats: null, alerts: [], gapAnalysis: null, accuracy: null }
    }
  },

  async getInventoryRecommendations(productId) {
    try {
      const response = await apiClient.get(`/api/v1/forecast/product/${productId}`, {
        params: { forecast_horizon_days: 30 },
      })
      const transformed = transformForecastResponse(response)
      return {
        alerts: transformed.alerts,
        inventory_level: response.current_inventory,
        reorder_point: response.reorder_recommendation,
      }
    } catch {
      return { alerts: [] }
    }
  },

  async getForecastAccuracy(productId, timeRange = '90d') {
    try {
      const response = await apiClient.get(`/api/v1/forecast/product/${productId}`, {
        params: { forecast_horizon_days: 30 },
      })
      return {
        mape: response.model_performances?.[0]?.mape ?? null,
        rmse: response.model_performances?.[0]?.rmse ?? null,
        confidence: response.final_confidence ?? null,
      }
    } catch {
      return { mape: null, rmse: null, confidence: null }
    }
  },

  async getDemandSupplyGap(productId, horizon = '30d') {
    try {
      const days = HORIZON_MAP[horizon] || 30
      const response = await apiClient.get(`/api/v1/forecast/product/${productId}`, {
        params: { forecast_horizon_days: days },
      })
      return transformForecastResponse(response).gapAnalysis
    } catch {
      return null
    }
  },

  async generateForecast(params) {
    const response = await apiClient.post('/api/v1/forecast', params)
    return response
  },

  async adjustForecast(productId, adjustments) {
    const response = await apiClient.post(`/api/v1/forecast/product/${productId}/adjust`, adjustments)
    return response
  },
}

export default forecastService
