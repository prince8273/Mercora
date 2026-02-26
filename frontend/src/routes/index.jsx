import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import AppShell from '../components/layouts/AppShell'
import AuthLayout from '../components/layouts/AuthLayout'
import PageErrorBoundary from '../components/feedback/ErrorBoundary/PageErrorBoundary'

// Pages
import LoginPage from '../pages/LoginPage'
import SignupPage from '../pages/SignupPage'
import OverviewPage from '../pages/OverviewPage'
import IntelligencePage from '../pages/IntelligencePage'
import PricingPage from '../pages/PricingPage'
import SentimentPage from '../pages/SentimentPage'
import ForecastPage from '../pages/ForecastPage'
import SettingsPage from '../pages/SettingsPage'

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <div className="loading-screen">Loading...</div>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}

function PublicRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <div className="loading-screen">Loading...</div>
  }

  if (isAuthenticated) {
    return <Navigate to="/overview" replace />
  }

  return children
}

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <AuthLayout>
              <LoginPage />
            </AuthLayout>
          </PublicRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <PublicRoute>
            <AuthLayout>
              <SignupPage />
            </AuthLayout>
          </PublicRoute>
        }
      />


      {/* Protected Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="overview" element={<PageErrorBoundary><OverviewPage /></PageErrorBoundary>} />
        <Route path="intelligence" element={<PageErrorBoundary><IntelligencePage /></PageErrorBoundary>} />
        <Route path="pricing" element={<PageErrorBoundary><PricingPage /></PageErrorBoundary>} />
        <Route path="sentiment" element={<PageErrorBoundary><SentimentPage /></PageErrorBoundary>} />
        <Route path="forecast" element={<PageErrorBoundary><ForecastPage /></PageErrorBoundary>} />
        <Route path="settings" element={<PageErrorBoundary><SettingsPage /></PageErrorBoundary>} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/overview" replace />} />
    </Routes>
  )
}
