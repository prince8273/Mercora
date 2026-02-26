/**
 * Authentication Service
 * Handles all authentication-related API calls
 */

import { apiClient } from '../lib/apiClient'

export const authService = {
  /**
   * Login with email and password
   */
  async login(email, password) {
    const response = await apiClient.post('/api/v1/auth/login', {
      email: email,
      password: password,
    })

    return response
  },

  /**
   * Register new user
   */
  async register(userData) {
    const response = await apiClient.post('/api/v1/auth/register', {
      email: userData.email,
      password: userData.password,
      full_name: userData.full_name,
      tenant_slug: userData.tenant_slug || userData.email.split('@')[0], // Generate slug from email if not provided
    })

    return response
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken) {
    const response = await apiClient.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    })

    return response
  },

  /**
   * Get current user info
   */
  async getCurrentUser(token = null) {
    // If token is provided, use it directly in the header
    const config = token ? {
      headers: {
        Authorization: `Bearer ${token}`
      }
    } : {}
    
    const response = await apiClient.get('/api/v1/auth/me', config)
    return response
  },

  /**
   * Logout user
   */
  async logout() {
    // Clear local storage
    localStorage.removeItem('token')
    localStorage.removeItem('tokenType')
    localStorage.removeItem('user')
    localStorage.removeItem('tenant')
    localStorage.removeItem('tenantId')
    
    // Optionally call backend logout endpoint if it exists
    try {
      await apiClient.post('/api/v1/auth/logout')
    } catch (error) {
      // Ignore errors on logout
      console.warn('Logout endpoint not available:', error)
    }
  },
}

export default authService
