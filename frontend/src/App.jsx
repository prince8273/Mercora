import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from './lib/queryClient'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { ToastProvider } from './components/organisms/ToastManager'
import GlobalErrorBoundary from './components/feedback/ErrorBoundary/GlobalErrorBoundary'
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
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </GlobalErrorBoundary>
  )
}

export default App
