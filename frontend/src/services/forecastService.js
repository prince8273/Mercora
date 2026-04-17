/**
 * Forecast Service
 * Handles all demand forecasting-related API calls
 */

import { apiClient } from '../lib/apiClient'

const HORIZON_MAP = { '7d': 7, '30d': 30, '60d': 60, '90d': 90 }

export const forecastService = {
  /**
   * Get demand forecast for a product
   * Called by useDemandForecast(productId, { horizon })
   */
  async getDemandForecast(productId, options = {}) {
    const horizon = options?.horizon || options || '30d'
    const days = HORIZON_MAP[horizon] || 30
    const response = await apiClient.get(`/api/v1/forecast/product/${productId}`, {
      params: { forecast_horizon_days: days },
    })
    return response
  },

  /**
   * Get inventory recommendations (alerts) for a product
   * Called by useInventoryRecommendations(productId)
   */
  async getInventoryRecommendations(productId) {
    try {
      const response = await apiClient.get(`/api/v1/forecast/product/${productId}`, {
        params: { forecast_horizon_days: 30 },
      })
      // Extract inventory alerts from forecast result
      return {
        alerts: response.alerts || [],
        inventory_level: response.current_inventory,
        reorder_point: response.reorder_point,
      }
    } catch {
      return { alerts: [] }
    }
  },

  /**
   * Get forecast accuracy metrics
   * Called by useForecastAccuracy(productId, timeRange)
   */
  async getForecastAccuracy(productId, timeRange = '90d') {
    try {
      const response = await apiClient.get(`/api/v1/forecast/product/${productId}`, {
        params: { forecast_horizon_days: 30 },
      })
      return {
        mape: response.accuracy?.mape || null,
        rmse: response.accuracy?.rmse || null,
        confidence: response.final_confidence || null,
      }
    } catch {
      return { mape: null, rmse: null, confidence: null }
    }
  },

  /**
   * Get demand-supply gap analysis
   * Called by useDemandSupplyGap(productId, horizon)
   */
  async getDemandSupplyGap(productId, horizon = '30d') {
    try {
      const days = HORIZON_MAP[horizon] || 30
      const response = await apiClient.get(`/api/v1/forecast/product/${productId}`, {
        params: { forecast_horizon_days: days },
      })
      return response.gapAnalysis || response.gap_analysis || null
    } catch {
      return null
    }
  },

  /**
   * Generate custom forecast (mutation)
   */
  async generateForecast(params) {
    const response = await apiClient.post('/api/v1/forecast', params)
    return response
  },

  /**
   * Adjust forecast parameters (mutation)
   */
  async adjustForecast(productId, adjustments) {
    const response = await apiClient.post(`/api/v1/forecast/product/${productId}/adjust`, adjustments)
    return response
  },
}

export default forecastService
