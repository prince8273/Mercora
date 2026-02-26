import React from 'react';
import { ProgressBar } from '../../../components/molecules/ProgressBar';
import { AgentStatus } from './AgentStatus';
import { Button } from '../../../components/atoms/Button';
import styles from './ExecutionPanel.module.css';

export const ExecutionPanel = ({
  progress = 0,
  status = 'idle',
  currentActivity = '',
  activityLog = [],
  estimatedTime = null,
  onCancel,
  error = null,
  onRetry,
  className = '',
  ...props
}) => {
  const formatTime = (seconds) => {
    if (!seconds || seconds < 0) return '--';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getProgressLabel = () => {
    if (error) return 'Error';
    if (progress === 100) return 'Complete';
    if (progress === 0) return 'Starting...';
    return `${Math.round(progress)}%`;
  };

  const getProgressVariant = () => {
    if (error) return 'error';
    if (progress === 100) return 'success';
    return 'primary';
  };

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <h3 className={styles.title}>Query Execution</h3>
        {estimatedTime && progress < 100 && !error && (
          <span className={styles.estimatedTime}>
            Est. {formatTime(estimatedTime)} remaining
          </span>
        )}
      </div>

      {/* Progress Bar */}
      <div className={styles.progressSection}>
        <ProgressBar
          value={progress}
          max={100}
          variant={getProgressVariant()}
          label={getProgressLabel()}
          showLabel
        />
      </div>

      {/* Agent Status */}
      <div className={styles.statusSection}>
        <AgentStatus
          status={error ? 'error' : status}
          currentActivity={error ? error : currentActivity}
          activityLog={activityLog}
        />
      </div>

      {/* Actions */}
      {!error && progress < 100 && onCancel && (
        <div className={styles.actions}>
          <Button
            variant="secondary"
            size="sm"
            onClick={onCancel}
          >
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Cancel Query
          </Button>
        </div>
      )}

      {/* Error Actions */}
      {error && onRetry && (
        <div className={styles.actions}>
          <Button
            variant="primary"
            size="sm"
            onClick={onRetry}
          >
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Retry Query
          </Button>
        </div>
      )}

      {/* Success Message */}
      {progress === 100 && !error && (
        <div className={styles.successMessage}>
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Query completed successfully</span>
        </div>
      )}
    </div>
  );
};
