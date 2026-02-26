/**
 * Forecast Service
 * Handles all demand forecasting-related API calls
 */

import { apiClient } from '../lib/apiClient'

export const forecastService = {
  /**
   * Get forecast for a product
   */
  async getForecast(productId, horizon = 30) {
    const response = await apiClient.get(`/api/v1/forecast/product/${productId}`, {
      params: { horizon },
    })

    return response
  },

  /**
   * Get seasonality pattern for a product
   */
  async getSeasonality(productId) {
    const response = await apiClient.get(`/api/v1/forecast/seasonality/${productId}`)
    return response
  },

  /**
   * Get inventory alerts
   */
  async getInventoryAlerts() {
    const response = await apiClient.get('/api/v1/forecast/alerts')
    return response
  },

  /**
   * Get forecast accuracy metrics
   */
  async getAccuracyMetrics(productId) {
    const response = await apiClient.get(`/api/v1/forecast/accuracy/${productId}`)
    return response
  },

  /**
   * Get demand-supply gap analysis
   */
  async getDemandSupplyGap(productId) {
    const response = await apiClient.get(`/api/v1/forecast/gap/${productId}`)
    return response
  },

  /**
   * Get reorder recommendations
   */
  async getReorderRecommendations() {
    const response = await apiClient.get('/api/v1/forecast/reorder')
    return response
  },
}

export default forecastService
