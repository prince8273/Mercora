/**
 * Query Service
 * Handles all intelligence query-related API calls
 */

import { apiClient } from '../lib/apiClient'

export const queryService = {
  /**
   * Execute a new query
   */
  async executeQuery(params) {
    const response = await apiClient.post('/api/v1/query', {
      query_text: params.query,  // Backend expects query_text, not query
      product_ids: params.product_ids || null,
      analysis_type: params.mode === 'deep' ? 'all' : 'all',  // Can be 'pricing', 'sentiment', or 'all'
    })

    return response
  },

  /**
   * Get query result by ID
   */
  async getQueryResult(queryId) {
    const response = await apiClient.get(`/api/v1/query/${queryId}`)
    return response
  },

  /**
   * Get query history
   */
  async getQueryHistory(params = {}) {
    const queryParams = {
      limit: params.limit || 10,
      offset: params.offset || 0,
      mode: params.mode,
    }

    const response = await apiClient.get('/api/v1/query/history', {
      params: queryParams,
    })

    return response
  },

  /**
   * Refine an existing query
   */
  async refineQuery(queryId, refinement) {
    const response = await apiClient.post(`/api/v1/query/${queryId}/refine`, {
      refinement,
    })

    return response
  },

  /**
   * Cancel a running query
   */
  async cancelQuery(queryId) {
    const response = await apiClient.post(`/api/v1/query/${queryId}/cancel`)
    return response
  },

  /**
   * Get query status
   */
  async getQueryStatus(queryId) {
    const response = await apiClient.get(`/api/v1/query/${queryId}/status`)
    return response
  },

  /**
   * Export query results
   */
  async exportResults(queryId, format) {
    const response = await apiClient.post(`/api/v1/query/${queryId}/export`, {
      format,
    })
    return response
  },

  /**
   * Get query by ID
   */
  async getQueryById(queryId) {
    const response = await apiClient.get(`/api/v1/query/${queryId}`)
    return response
  },

  /**
   * Get query suggestions
   */
  async getQuerySuggestions(input) {
    const response = await apiClient.get('/api/v1/query/suggestions', {
      params: { q: input },
    })
    return response
  },
}

export default queryService
