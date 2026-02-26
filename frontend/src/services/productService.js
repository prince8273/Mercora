/**
 * Product Service
 * Handles all product-related API calls
 */

import { apiClient } from '../lib/apiClient'

export const productService = {
  /**
   * Get all products
   */
  async getProducts(params = {}) {
    const response = await apiClient.get('/api/v1/products', {
      params: {
        skip: params.skip || 0,
        limit: params.limit || 100,
      },
    })
    return response
  },

  /**
   * Get a single product by ID
   */
  async getProduct(productId) {
    const response = await apiClient.get(`/api/v1/products/${productId}`)
    return response
  },

  /**
   * Create a new product
   */
  async createProduct(productData) {
    const response = await apiClient.post('/api/v1/products', productData)
    return response
  },

  /**
   * Update a product
   */
  async updateProduct(productId, productData) {
    const response = await apiClient.put(`/api/v1/products/${productId}`, productData)
    return response
  },

  /**
   * Delete a product
   */
  async deleteProduct(productId) {
    const response = await apiClient.delete(`/api/v1/products/${productId}`)
    return response
  },
}

export default productService
