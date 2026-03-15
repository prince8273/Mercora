import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import AppShell from '../components/layouts/AppShell'
import AuthLayout from '../components/layouts/AuthLayout'
import PageErrorBoundary from '../components/feedback/ErrorBoundary/PageErrorBoundary'

// Pages
import LandingPage from '../pages/LandingPage'
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
    return <Navigate to="/" replace />
  }

  return children
}

function PublicRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <div className="loading-screen">Loading...</div>
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard/overview" replace />
  }

  return children
}

export default function AppRoutes() {
  return (
    <Routes>
      {/* Landing Page - Public */}
      <Route path="/" element={<LandingPage />} />
      
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
        path="/dashboard"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard/overview" replace />} />
        <Route path="overview" element={<PageErrorBoundary><OverviewPage /></PageErrorBoundary>} />
        <Route path="intelligence" element={<PageErrorBoundary><IntelligencePage /></PageErrorBoundary>} />
        <Route path="pricing" element={<PageErrorBoundary><PricingPage /></PageErrorBoundary>} />
        <Route path="sentiment" element={<PageErrorBoundary><SentimentPage /></PageErrorBoundary>} />
        <Route path="forecast" element={<PageErrorBoundary><ForecastPage /></PageErrorBoundary>} />
        <Route path="settings" element={<PageErrorBoundary><SettingsPage /></PageErrorBoundary>} />
      </Route>

      {/* Redirect old routes */}
      <Route path="/overview" element={<Navigate to="/dashboard/overview" replace />} />
      <Route path="/intelligence" element={<Navigate to="/dashboard/intelligence" replace />} />
      <Route path="/pricing" element={<Navigate to="/dashboard/pricing" replace />} />
      <Route path="/sentiment" element={<Navigate to="/dashboard/sentiment" replace />} />
      <Route path="/forecast" element={<Navigate to="/dashboard/forecast" replace />} />
      <Route path="/settings" element={<Navigate to="/dashboard/settings" replace />} />

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
