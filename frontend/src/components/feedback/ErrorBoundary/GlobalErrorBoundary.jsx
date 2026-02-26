import React from 'react';

class GlobalErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console (in production, send to error tracking service like Sentry)
    console.error('Global Error Boundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });

    // TODO: Send to error tracking service
    // if (process.env.NODE_ENV === 'production') {
    //   Sentry.captureException(error, { extra: errorInfo });
    // }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <GlobalErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onReset={this.handleReset}
        />
      );
    }

    return this.props.children;
  }
}

function GlobalErrorFallback({ error, errorInfo, onReset }) {
  return (
    <div style={styles.container}>
      <div style={styles.content}>
        <svg
          style={styles.icon}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <h1 style={styles.title}>Something went wrong</h1>
        <p style={styles.message}>
          We're sorry, but something unexpected happened. The error has been logged
          and we'll look into it.
        </p>
        {process.env.NODE_ENV === 'development' && error && (
          <details style={styles.details}>
            <summary style={styles.summary}>Error Details (Development Only)</summary>
            <pre style={styles.errorText}>
              {error.toString()}
              {errorInfo && errorInfo.componentStack}
            </pre>
          </details>
        )}
        <button onClick={onReset} style={styles.button}>
          Go to Home Page
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f9fafb',
    padding: '1rem',
  },
  content: {
    maxWidth: '32rem',
    width: '100%',
    textAlign: 'center',
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '0.5rem',
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
  },
  icon: {
    width: '4rem',
    height: '4rem',
    color: '#ef4444',
    margin: '0 auto 1rem',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: '600',
    color: '#111827',
    marginBottom: '0.5rem',
  },
  message: {
    fontSize: '1rem',
    color: '#6b7280',
    marginBottom: '1.5rem',
    lineHeight: '1.5',
  },
  details: {
    marginTop: '1.5rem',
    textAlign: 'left',
    backgroundColor: '#f3f4f6',
    padding: '1rem',
    borderRadius: '0.375rem',
    marginBottom: '1.5rem',
  },
  summary: {
    cursor: 'pointer',
    fontWeight: '500',
    marginBottom: '0.5rem',
  },
  errorText: {
    fontSize: '0.875rem',
    color: '#ef4444',
    overflow: 'auto',
    maxHeight: '12rem',
  },
  button: {
    backgroundColor: '#3b82f6',
    color: 'white',
    padding: '0.75rem 1.5rem',
    borderRadius: '0.375rem',
    border: 'none',
    fontSize: '1rem',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
};

export default GlobalErrorBoundary;
