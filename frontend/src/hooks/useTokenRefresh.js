/**
 * useTokenRefresh
 *
 * Keeps the session alive while the user is active on the dashboard.
 * Every REFRESH_INTERVAL ms it calls POST /auth/refresh with the current
 * Bearer token and stores the new token — completely transparent to the user.
 *
 * Logic:
 *  - Token lifetime on the backend: 8 hours
 *  - We refresh every 20 minutes so the token never gets close to expiry
 *    as long as the tab is open and the user is logged in.
 *  - If the refresh fails (e.g. server restart invalidated the token) the
 *    apiClient's 401 interceptor will redirect to /login automatically.
 */
import { useEffect, useRef } from 'react'
import { apiClient } from '../lib/apiClient'

const REFRESH_INTERVAL = 20 * 60 * 1000 // 20 minutes in ms

export function useTokenRefresh(isAuthenticated) {
  const timerRef = useRef(null)

  useEffect(() => {
    if (!isAuthenticated) return

    const refresh = async () => {
      const token = localStorage.getItem('token')
      if (!token) return

      try {
        const response = await apiClient.post('/api/v1/auth/refresh')
        if (response?.access_token) {
          localStorage.setItem('token', response.access_token)
        }
      } catch (err) {
        // 401 is handled by apiClient interceptor (redirects to /login)
        // Any other error: log and let the next interval retry
        console.warn('[useTokenRefresh] refresh failed:', err?.message)
      }
    }

    // Refresh immediately on mount (handles page reload after long idle)
    refresh()

    timerRef.current = setInterval(refresh, REFRESH_INTERVAL)

    return () => clearInterval(timerRef.current)
  }, [isAuthenticated])
}
