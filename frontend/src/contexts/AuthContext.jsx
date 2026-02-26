import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/authService'

const AuthContext = createContext(null)

// Export AuthContext for useAuth hook
export { AuthContext }

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [tenant, setTenant] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')
    const storedTenant = localStorage.getItem('tenant')

    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser))
        setTenant(storedTenant ? JSON.parse(storedTenant) : null)
        setIsAuthenticated(true)
      } catch (error) {
        console.error('Failed to parse stored user data:', error)
        logout()
      }
    }

    setIsLoading(false)
  }, [])

  const login = async (email, password) => {
    try {
      console.log('Starting login process for:', email)
      
      // Clear any existing data first
      localStorage.removeItem('token')
      localStorage.removeItem('tokenType')
      localStorage.removeItem('user')
      localStorage.removeItem('tenantId')
      localStorage.removeItem('tenant')
      setUser(null)
      setTenant(null)
      setIsAuthenticated(false)
      console.log('Cleared previous session data')
      
      // Step 1: Login and get token
      const tokenResponse = await authService.login(email, password)
      console.log('Token response received:', { hasToken: !!tokenResponse.access_token })
      
      const { access_token, token_type } = tokenResponse

      if (!access_token) {
        throw new Error('No access token received from server')
      }

      // Step 2: Store token FIRST before any other API calls
      localStorage.setItem('token', access_token)
      localStorage.setItem('tokenType', token_type)
      console.log('Token stored in localStorage')

      // Step 3: Fetch user data using the token (pass token directly)
      console.log('Fetching user data...')
      const userData = await authService.getCurrentUser(access_token)
      console.log('User data received:', { 
        email: userData.email, 
        id: userData.id,
        full_name: userData.full_name,
        tenant_id: userData.tenant_id
      })

      // Step 4: Store user data
      localStorage.setItem('user', JSON.stringify(userData))

      if (userData.tenant_id) {
        localStorage.setItem('tenantId', userData.tenant_id)
        console.log('Tenant ID stored:', userData.tenant_id)
      }

      setUser(userData)
      setIsAuthenticated(true)
      console.log('Login successful! User set:', userData.email)

      return { success: true }
    } catch (error) {
      console.error('Login failed:', error)
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      })
      
      // Clear any partial data
      localStorage.removeItem('token')
      localStorage.removeItem('tokenType')
      localStorage.removeItem('user')
      localStorage.removeItem('tenantId')
      
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Login failed. Please try again.',
      }
    }
  }

  const signup = async (userData) => {
    try {
      // Step 1: Register user
      await authService.register(userData)

      // Step 2: Login with the new credentials
      const loginResult = await login(userData.email, userData.password)

      return loginResult
    } catch (error) {
      console.error('Signup failed:', error)
      return {
        success: false,
        error: error.response?.data?.detail || 'Signup failed',
      }
    }
  }

  const logout = () => {
    authService.logout()

    setUser(null)
    setTenant(null)
    setIsAuthenticated(false)

    navigate('/login')
  }

  const switchTenant = async (tenantId) => {
    try {
      const response = await apiClient.post('/api/v1/auth/switch-tenant', {
        tenant_id: tenantId,
      })

      const { tenant: newTenant } = response

      localStorage.setItem('tenant', JSON.stringify(newTenant))
      localStorage.setItem('tenantId', newTenant.id)
      setTenant(newTenant)

      return { success: true }
    } catch (error) {
      console.error('Failed to switch tenant:', error)
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to switch tenant',
      }
    }
  }

  const value = {
    user,
    tenant,
    isAuthenticated,
    isLoading,
    login,
    signup,
    logout,
    switchTenant,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// Export useAuth hook separately to avoid Fast Refresh issues
export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
