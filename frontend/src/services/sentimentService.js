/**
 * Sentiment Service
 * Handles all sentiment analysis-related API calls
 */

import { apiClient } from '../lib/apiClient'

export const sentimentService = {
  /**
   * Get sentiment overview for a product
   */
  async getSentimentOverview(productId, filters = {}) {
    const { timeRange = '30d', ...rest } = filters
    const response = await apiClient.get(`/api/v1/sentiment/product/${productId}`, {
      params: { time_range: timeRange, ...rest },
    })

    const dist = response.sentiment_distribution || {}
    const total = response.total_reviews || 1
    const pos = dist.positive || 0
    const neu = dist.neutral || 0
    const neg = dist.negative || 0

    // Use one decimal place to avoid rounding to 0%
    const posP = parseFloat(((pos / total) * 100).toFixed(1))
    const neuP = parseFloat(((neu / total) * 100).toFixed(1))
    const negP = parseFloat(((neg / total) * 100).toFixed(1))

    // aggregate_sentiment is -1 to 1, convert to 0-100
    const score = Math.round(((response.aggregate_sentiment || 0) + 1) / 2 * 100)

    return {
      overallScore: score,
      trend: 0,
      distribution: {
        positive: posP,
        neutral:  neuP,
        negative: negP,
      },
      totalReviews: response.total_reviews || 0,
      confidenceScore: response.confidence_score || 0,
      _raw: response,
    }
  },

  /**
   * Get sentiment analysis for a product (alias for getSentimentOverview)
   */
  async getSentimentAnalysis(productId) {
    const response = await apiClient.get(`/api/v1/sentiment/product/${productId}`)
    return response
  },

  /**
   * Get complaint analysis for a product
   * Builds categories + trend from negative reviews
   */
  async getComplaintAnalysis(productId, filters = {}) {
    const { timeRange = '30d' } = filters
    // Fetch reviews and build complaint data client-side
    const response = await apiClient.get(`/api/v1/sentiment/reviews/${productId}`, {
      params: { time_range: timeRange, limit: 200 },
    })

    const reviews = response.reviews || []
    const negativeReviews = reviews.filter(r => r.sentiment === 'negative')

    if (negativeReviews.length === 0) {
      return { categories: [], trend: [], complaints: [], totalComplaints: 0, criticalCount: 0 }
    }

    // Keyword-based categorisation
    const CATEGORIES = {
      'Quality':    ['quality', 'cheap', 'broke', 'broken', 'defective', 'poor quality', 'flimsy'],
      'Shipping':   ['shipping', 'delivery', 'late', 'delayed', 'arrived', 'packaging', 'damaged'],
      'Value':      ['price', 'expensive', 'overpriced', 'not worth', 'waste of money'],
      'Fit/Size':   ['size', 'fit', 'small', 'large', 'tight', 'loose', 'sizing'],
      'Performance':['doesn\'t work', 'not working', 'stopped', 'failed', 'issue', 'problem'],
      'Other':      [],
    }

    const catCounts = {}
    const complaintItems = []

    negativeReviews.forEach(r => {
      const text = (r.text || '').toLowerCase()
      let matched = false
      for (const [cat, keywords] of Object.entries(CATEGORIES)) {
        if (cat === 'Other') continue
        if (keywords.some(k => text.includes(k))) {
          catCounts[cat] = (catCounts[cat] || 0) + 1
          complaintItems.push({ text: r.text?.slice(0, 80), count: 1, category: cat })
          matched = true
          break
        }
      }
      if (!matched) {
        catCounts['Other'] = (catCounts['Other'] || 0) + 1
        complaintItems.push({ text: r.text?.slice(0, 80), count: 1, category: 'Other' })
      }
    })

    const categories = Object.entries(catCounts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)

    // Build weekly trend from created_at
    const weekMap = {}
    negativeReviews.forEach(r => {
      if (!r.created_at) return
      const d = new Date(r.created_at)
      const week = d.toISOString().slice(0, 10)
      weekMap[week] = (weekMap[week] || 0) + 1
    })
    const trend = Object.entries(weekMap)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, count]) => ({ date, count }))

    const criticalCount = negativeReviews.filter(r => r.rating === 1).length

    return {
      categories,
      trend,
      complaints: complaintItems,
      totalComplaints: negativeReviews.length,
      criticalCount,
    }
  },

  /**
   * Get reviews for a product
   */
  async getReviews(productId, filters = {}) {
    const { timeRange = '30d', ...rest } = filters
    const response = await apiClient.get(`/api/v1/sentiment/reviews/${productId}`, {
      params: { time_range: timeRange, limit: 200, ...rest },
    })
    return response
  },

  /**
   * Get theme breakdown for a product (extracted from sentiment result)
   */
  async getThemeBreakdown(productId, filters = {}) {
    const { timeRange = '30d' } = filters
    const response = await apiClient.get(`/api/v1/sentiment/product/${productId}`, {
      params: { time_range: timeRange },
    })
    const topics = response.top_topics || []
    const totalMentions = topics.reduce((s, t) => s + (t.review_count || 0), 0) || 1
    return {
      themes: topics.map(t => ({
        name: t.keywords?.[0] || `Topic ${t.topic_id}`,
        count: t.review_count || 0,
        percentage: parseFloat(((t.review_count || 0) / totalMentions * 100).toFixed(1)),
        keywords: t.keywords || [],
      }))
    }
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
