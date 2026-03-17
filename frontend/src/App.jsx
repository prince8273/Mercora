import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './lib/queryClient'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { ToastProvider } from './components/organisms/ToastManager'
import GlobalErrorBoundary from './components/feedback/ErrorBoundary/GlobalErrorBoundary'
import './i18n/config' // Initialize i18n
// import { ConnectionStatus } from './components/molecules/ConnectionStatus'
import AppRoutes from './routes'

function App() {
  return (
    <GlobalErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ThemeProvider>
            <ToastProvider>
              <AuthProvider>
                {/* <ConnectionStatus /> */}
                <AppRoutes />
              </AuthProvider>
            </ToastProvider>
          </ThemeProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </GlobalErrorBoundary>
  )
}

export default App
