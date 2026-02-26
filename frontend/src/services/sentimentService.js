/**
 * Sentiment Service
 * Handles all sentiment analysis-related API calls
 */

import { apiClient } from '../lib/apiClient'

export const sentimentService = {
  /**
   * Get sentiment analysis for a product
   */
  async getSentimentAnalysis(productId) {
    const response = await apiClient.get(`/api/v1/sentiment/product/${productId}`)
    return response
  },

  /**
   * Get reviews for a product
   */
  async getReviews(productId, filters = {}) {
    const response = await apiClient.get(`/api/v1/sentiment/reviews/${productId}`, {
      params: filters,
    })

    return response
  },

  /**
   * Get theme breakdown for a product
   */
  async getThemeBreakdown(productId) {
    const response = await apiClient.get(`/api/v1/sentiment/themes/${productId}`)
    return response
  },

  /**
   * Get feature requests for a product
   */
  async getFeatureRequests(productId) {
    const response = await apiClient.get(`/api/v1/sentiment/features/${productId}`)
    return response
  },

  /**
   * Get complaints for a product
   */
  async getComplaints(productId) {
    const response = await apiClient.get(`/api/v1/sentiment/complaints/${productId}`)
    return response
  },

  /**
   * Get sentiment trends over time
   */
  async getSentimentTrends(productId, days = 30) {
    const response = await apiClient.get(`/api/v1/sentiment/trends/${productId}`, {
      params: { days },
    })

    return response
  },
}

export default sentimentService
