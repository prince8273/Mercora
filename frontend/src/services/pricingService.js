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
   * Get price trends for a product (renamed from getPriceHistory)
   */
  async getPriceTrends(productId, timeRange = '30d') {
    // Convert timeRange to days
    const daysMap = {
      '7d': 7,
      '30d': 30,
      '60d': 60,
      '90d': 90,
      '1y': 365
    };
    const days = daysMap[timeRange] || 30;
    
    const response = await apiClient.get(`/api/v1/pricing/history/${productId}`, {
      params: { days },
    })

    // Transform the data to match what PriceTrendChart expects
    if (response && response.trends) {
      const transformedTrends = response.trends.map(item => ({
        date: item.date,
        yourPrice: item.price,  // Transform 'price' to 'yourPrice'
        competitor1: item.competitor_avg,  // Transform 'competitor_avg' to 'competitor1'
        marketDemand: item.market_demand,
        reason: item.reason
      }));
      
      return {
        ...response,
        trends: transformedTrends,
        data: transformedTrends  // Also provide as 'data' for compatibility
      };
    }

    return response
  },

  /**
   * Get competitor matrix
   */
  async getCompetitorMatrix(productId) {
    const response = await apiClient.get(`/api/v1/pricing/competitors/${productId}`)
    return response
  },

  /**
   * Get pricing recommendations (renamed from getPriceRecommendations)
   */
  async getPricingRecommendations(productId) {
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
   * Get promotion effectiveness for a product (renamed from getPromotionEffectiveness)
   */
  async getPromotionAnalysis(filters = {}) {
    // For now, return mock data since we don't have a specific product ID
    // In a real implementation, this would use the filters to query promotions
    const response = {
      promotions: [
        {
          id: "promo_001",
          name: "Flash Sale 15% Off",
          discount_percent: 15,
          start_date: "2026-02-01",
          end_date: "2026-02-07",
          metrics: {
            revenue: 12500,
            units_sold: 125,
            conversion_rate: 0.12
          },
          effectiveness: "high"
        },
        {
          id: "promo_002", 
          name: "Bundle Deal",
          discount_percent: 10,
          start_date: "2026-01-15",
          end_date: "2026-01-31",
          metrics: {
            revenue: 6800,
            units_sold: 68,
            conversion_rate: 0.09
          },
          effectiveness: "medium"
        }
      ],
      total_revenue: 19300,
      avg_effectiveness: 0.75
    };
    
    return response;
  },

  /**
   * Apply pricing recommendation
   */
  async applyPricing(productId, newPrice) {
    const response = await apiClient.put(`/api/v1/pricing/apply/${productId}`, {
      new_price: newPrice
    })
    return response
  },

  /**
   * Get competitor pricing data
   */
  async getCompetitorPricing(productId, filters = {}) {
    // Mock competitor data
    const response = {
      product_id: productId,
      competitors: [
        {
          name: "Competitor A",
          price: 89.99,
          market_share: 0.25,
          rating: 4.2
        },
        {
          name: "Competitor B", 
          price: 94.50,
          market_share: 0.18,
          rating: 4.0
        }
      ],
      market_position: "competitive",
      price_rank: 2
    };
    
    return response;
  },
}

export default pricingService
