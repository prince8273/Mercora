import React from 'react';
import { StatusIndicator } from '../../../components/molecules/StatusIndicator';
import styles from './AgentStatus.module.css';

export const AgentStatus = ({
  status = 'idle', // 'active', 'idle', 'error'
  currentActivity = '',
  activityLog = [],
  className = '',
  ...props
}) => {
  const getStatusLabel = (status) => {
    const labels = {
      active: 'Active',
      idle: 'Idle',
      error: 'Error',
    };
    return labels[status] || 'Unknown';
  };

  const getStatusMessage = (status) => {
    const messages = {
      active: 'Agent is processing your query...',
      idle: 'Agent is ready to process queries',
      error: 'Agent encountered an error',
    };
    return messages[status] || '';
  };

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <div className={styles.statusRow}>
          <StatusIndicator
            status={status}
            pulse={status === 'active'}
            size="md"
            label={getStatusLabel(status)}
          />
        </div>
        {currentActivity && (
          <p className={styles.currentActivity}>{currentActivity}</p>
        )}
        {!currentActivity && (
          <p className={styles.statusMessage}>{getStatusMessage(status)}</p>
        )}
      </div>

      {activityLog && activityLog.length > 0 && (
        <div className={styles.activityLog}>
          <h4 className={styles.logTitle}>Activity Log</h4>
          <ul className={styles.logList}>
            {activityLog.map((activity, index) => (
              <li key={index} className={styles.logItem}>
                <span className={styles.logTimestamp}>
                  {formatTimestamp(activity.timestamp)}
                </span>
                <span className={styles.logMessage}>{activity.message}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Helper function to format timestamp
const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};
