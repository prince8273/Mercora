/**
 * Pricing Service
 * Handles all pricing analysis-related API calls
 */

import { apiClient } from '../lib/apiClient'

export const pricingService = {
  /**
   * Get pricing analysis for a product
   */
  async getPricingAnalysis(productId) {
    const response = await apiClient.get('/api/v1/pricing/analysis', {
      params: { product_id: productId },
    })

    return response
  },

  /**
   * Get price history for a product
   */
  async getPriceHistory(productId, days = 30) {
    const response = await apiClient.get(`/api/v1/pricing/history/${productId}`, {
      params: { days },
    })

    return response
  },

  /**
   * Get competitor matrix
   */
  async getCompetitorMatrix(productIds) {
    const response = await apiClient.post('/api/v1/pricing/competitors', {
      product_ids: productIds,
    })

    return response
  },

  /**
   * Get pricing recommendations
   */
  async getPriceRecommendations(productId) {
    const response = await apiClient.get(`/api/v1/pricing/recommendations/${productId}`)
    return response
  },

  /**
   * Get all products for pricing
   */
  async getProducts() {
    const response = await apiClient.get('/api/v1/products')
    return response
  },

  /**
   * Get promotion effectiveness
   */
  async getPromotionEffectiveness(productId) {
    const response = await apiClient.get(`/api/v1/pricing/promotions/${productId}`)
    return response
  },
}

export default pricingService
