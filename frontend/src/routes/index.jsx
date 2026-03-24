import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTokenRefresh } from '../hooks/useTokenRefresh'
import AppShell from '../components/layouts/AppShell'
import AuthLayout from '../components/layouts/AuthLayout'
import PageErrorBoundary from '../components/feedback/ErrorBoundary/PageErrorBoundary'

// Pages
import ModernLandingPage from '../pages/ModernLandingPage'
import AboutUsPage from '../pages/AboutUsPage'
import LoginPage from '../pages/LoginPage'
import SignupPage from '../pages/SignupPage'
import OverviewPage from '../pages/OverviewPage'
import IntelligencePage from '../pages/IntelligencePage'
import PricingPage from '../pages/PricingPage'
import SentimentPage from '../pages/SentimentPage'
import ForecastPage from '../pages/ForecastPage'
import SettingsPage from '../pages/SettingsPage'
import QueryBreakdownPage from '../pages/QueryBreakdownPage'
import { DemoBackgroundBeams } from '../components/demo/DemoBackgroundBeams'
import VideoDemo from '../pages/VideoDemo'
import Simple11xDemo from '../pages/Simple11xDemo'

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()

  // Silently refresh the token every 20 min while user is on the dashboard
  useTokenRefresh(isAuthenticated)

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
      {/* Modern Landing Page - Public (Main Landing Page) */}
      <Route path="/" element={<ModernLandingPage />} />
      <Route path="/modern" element={<ModernLandingPage />} />

      {/* About Us Page - Public */}
      <Route path="/about-us" element={<AboutUsPage />} />

      {/* Demo BackgroundBeams - Public */}
      <Route path="/demo-beams" element={<DemoBackgroundBeams />} />

      {/* Video Demo - Public */}
      <Route path="/video-demo" element={<VideoDemo />} />

      {/* Simple 11x Demo - Public */}
      <Route path="/11x-demo" element={<Simple11xDemo />} />

      {/* Temporary redirect for /landing to main page */}
      <Route path="/landing" element={<Navigate to="/" replace />} />

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
        <Route path="intelligence/breakdown" element={<PageErrorBoundary><QueryBreakdownPage /></PageErrorBoundary>} />
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
