/**
 * Dashboard Service
 * Handles all dashboard-related API calls
 */

import { apiClient } from '../lib/apiClient'

export const dashboardService = {
  /**
   * Get dashboard overview
   */
  async getOverview(filters = {}) {
    const response = await apiClient.get('/api/v1/dashboard/stats', { params: filters })
    return response
  },

  /**
   * Get KPI metrics
   */
  async getKPIs(dateRange = null) {
    const params = {}
    if (dateRange) {
      params.start_date = dateRange.start
      params.end_date = dateRange.end
    }

    const response = await apiClient.get('/api/v1/dashboard/kpis', { params })
    return response
  },

  /**
   * Get KPI metrics (alias for compatibility)
   */
  async getKPIMetrics(timeRange = '30d') {
    const response = await apiClient.get('/api/v1/dashboard/kpis')
    return response
  },

  /**
   * Get trend data
   */
  async getTrends(dateRange = null) {
    const params = {}
    if (dateRange) {
      params.start_date = dateRange.start
      params.end_date = dateRange.end
    }

    const response = await apiClient.get('/api/v1/dashboard/trends', { params })
    return response
  },

  /**
   * Get trend data (alias for compatibility)
   */
  async getTrendData(metric, timeRange = '30d') {
    const params = { days: timeRange === '30d' ? 30 : 7 }
    const response = await apiClient.get('/api/v1/dashboard/trends', { params })
    return response
  },

  /**
   * Get alerts
   */
  async getAlerts() {
    const response = await apiClient.get('/api/v1/dashboard/alerts')
    return response
  },

  /**
   * Get quick insights
   */
  async getQuickInsights() {
    const response = await apiClient.get('/api/v1/dashboard/insights')
    return response
  },

  /**
   * Get recent activity
   */
  async getRecentActivity(limit = 10) {
    const response = await apiClient.get('/api/v1/dashboard/recent-activity', { params: { limit } })
    return response
  },

  /**
   * Get dashboard summary
   */
  async getSummary(dateRange = null) {
    const params = {}
    if (dateRange) {
      params.start_date = dateRange.start
      params.end_date = dateRange.end
    }

    const response = await apiClient.get('/api/v1/dashboard/summary', { params })
    return response
  },
}

export default dashboardService
