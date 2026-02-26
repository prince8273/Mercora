import React, { useState } from 'react';
import { StatusIndicator } from '../../../components/molecules/StatusIndicator';
import { LoadingSkeleton } from '../../../components/molecules/LoadingSkeleton';
import styles from './AlertPanel.module.css';

export const AlertPanel = ({
  alerts = [],
  loading = false,
  onDismiss,
  onAlertClick,
  className = '',
  ...props
}) => {
  const [expandedAlert, setExpandedAlert] = useState(null);

  const handleAlertClick = (alert) => {
    setExpandedAlert(expandedAlert === alert.id ? null : alert.id);
    if (onAlertClick) {
      onAlertClick(alert);
    }
  };

  const handleDismiss = (e, alertId) => {
    e.stopPropagation();
    if (onDismiss) {
      onDismiss(alertId);
    }
  };

  const getPriorityStatus = (priority) => {
    const statusMap = {
      critical: 'error',
      high: 'error',
      warning: 'warning',
      medium: 'warning',
      info: 'idle',
      low: 'idle',
    };
    return statusMap[priority?.toLowerCase()] || 'idle';
  };

  const getPriorityLabel = (priority) => {
    return priority?.charAt(0).toUpperCase() + priority?.slice(1).toLowerCase();
  };

  if (loading) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Alerts</h3>
        </div>
        <div className={styles.content}>
          <LoadingSkeleton variant="list" count={3} />
        </div>
      </div>
    );
  }

  if (!alerts || alerts.length === 0) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Alerts</h3>
        </div>
        <div className={styles.content}>
          <div className={styles.emptyState}>
            <svg
              className={styles.emptyIcon}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className={styles.emptyText}>No alerts at this time</p>
            <p className={styles.emptySubtext}>
              You're all caught up! We'll notify you when something needs attention.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <h3 className={styles.title}>Alerts</h3>
        <span className={styles.badge}>{alerts.length}</span>
      </div>
      <div className={styles.content}>
        <ul className={styles.alertList} role="list">
          {alerts.map((alert) => (
            <li
              key={alert.id}
              className={`${styles.alertItem} ${
                expandedAlert === alert.id ? styles.expanded : ''
              }`}
              onClick={() => handleAlertClick(alert)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleAlertClick(alert);
                }
              }}
              aria-expanded={expandedAlert === alert.id}
            >
              <div className={styles.alertHeader}>
                <div className={styles.alertInfo}>
                  <StatusIndicator
                    status={getPriorityStatus(alert.priority)}
                    pulse={alert.priority === 'critical'}
                    size="md"
                    tooltip={`${getPriorityLabel(alert.priority)} priority`}
                  />
                  <div className={styles.alertContent}>
                    <h4 className={styles.alertTitle}>{alert.title}</h4>
                    <p className={styles.alertMessage}>{alert.message}</p>
                  </div>
                </div>
                <div className={styles.alertActions}>
                  {alert.timestamp && (
                    <span className={styles.timestamp}>
                      {formatTimestamp(alert.timestamp)}
                    </span>
                  )}
                  <button
                    className={styles.dismissButton}
                    onClick={(e) => handleDismiss(e, alert.id)}
                    aria-label="Dismiss alert"
                    title="Dismiss"
                  >
                    <svg
                      width="16"
                      height="16"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              </div>

              {expandedAlert === alert.id && alert.details && (
                <div className={styles.alertDetails}>
                  <p className={styles.detailsText}>{alert.details}</p>
                  {alert.actionUrl && (
                    <a
                      href={alert.actionUrl}
                      className={styles.actionLink}
                      onClick={(e) => e.stopPropagation()}
                    >
                      {alert.actionLabel || 'View Details'}
                      <svg
                        width="16"
                        height="16"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </a>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

// Helper function to format timestamp
const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric' 
  });
};
