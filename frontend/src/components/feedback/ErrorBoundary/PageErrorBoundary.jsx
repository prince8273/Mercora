import React from 'react';
import { useNavigate } from 'react-router-dom';

class PageErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Page Error Boundary caught an error:', error, errorInfo);
    this.setState({ error });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <PageErrorFallback
          error={this.state.error}
          onReset={this.handleReset}
          onGoBack={this.props.onGoBack}
        />
      );
    }

    return this.props.children;
  }
}

function PageErrorFallback({ error, onReset, onGoBack }) {
  const navigate = useNavigate();

  const handleGoBack = () => {
    if (onGoBack) {
      onGoBack();
    } else {
      navigate(-1);
    }
  };

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
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h2 style={styles.title}>Page Error</h2>
        <p style={styles.message}>
          This page encountered an error. You can try again or go back to the previous page.
        </p>
        {process.env.NODE_ENV === 'development' && error && (
          <details style={styles.details}>
            <summary style={styles.summary}>Error Details</summary>
            <pre style={styles.errorText}>{error.toString()}</pre>
          </details>
        )}
        <div style={styles.buttonGroup}>
          <button onClick={handleGoBack} style={styles.secondaryButton}>
            Go Back
          </button>
          <button onClick={onReset} style={styles.primaryButton}>
            Try Again
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '50vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
  },
  content: {
    maxWidth: '28rem',
    width: '100%',
    textAlign: 'center',
  },
  icon: {
    width: '3rem',
    height: '3rem',
    color: '#f59e0b',
    margin: '0 auto 1rem',
  },
  title: {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: '#111827',
    marginBottom: '0.5rem',
  },
  message: {
    fontSize: '0.875rem',
    color: '#6b7280',
    marginBottom: '1.5rem',
    lineHeight: '1.5',
  },
  details: {
    marginBottom: '1.5rem',
    textAlign: 'left',
    backgroundColor: '#fef3c7',
    padding: '1rem',
    borderRadius: '0.375rem',
  },
  summary: {
    cursor: 'pointer',
    fontWeight: '500',
    marginBottom: '0.5rem',
    color: '#92400e',
  },
  errorText: {
    fontSize: '0.75rem',
    color: '#92400e',
    overflow: 'auto',
    maxHeight: '8rem',
  },
  buttonGroup: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'center',
  },
  primaryButton: {
    backgroundColor: '#3b82f6',
    color: 'white',
    padding: '0.625rem 1.25rem',
    borderRadius: '0.375rem',
    border: 'none',
    fontSize: '0.875rem',
    fontWeight: '500',
    cursor: 'pointer',
  },
  secondaryButton: {
    backgroundColor: 'white',
    color: '#374151',
    padding: '0.625rem 1.25rem',
    borderRadius: '0.375rem',
    border: '1px solid #d1d5db',
    fontSize: '0.875rem',
    fontWeight: '500',
    cursor: 'pointer',
  },
};

// Wrapper component to use hooks
export default function PageErrorBoundaryWrapper({ children }) {
  const navigate = useNavigate();
  
  return (
    <PageErrorBoundary onGoBack={() => navigate(-1)}>
      {children}
    </PageErrorBoundary>
  );
}
