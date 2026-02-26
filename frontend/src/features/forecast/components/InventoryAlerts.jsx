import { useState, useMemo } from 'react';
import { StatusIndicator } from '../../../components/molecules/StatusIndicator/StatusIndicator';
import styles from './InventoryAlerts.module.css';

export default function InventoryAlerts({ data, isLoading, onDismiss, onTakeAction }) {
  const [filter, setFilter] = useState('all');

  const filteredAlerts = useMemo(() => {
    if (!data?.alerts) return [];

    if (filter === 'all') return data.alerts;
    return data.alerts.filter((alert) => alert.priority === filter);
  }, [data, filter]);

  const priorityCounts = useMemo(() => {
    if (!data?.alerts) return { critical: 0, warning: 0, info: 0 };

    return data.alerts.reduce(
      (acc, alert) => {
        acc[alert.priority] = (acc[alert.priority] || 0) + 1;
        return acc;
      },
      { critical: 0, warning: 0, info: 0 }
    );
  }, [data]);

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'critical':
        return '🚨';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '📋';
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!data?.alerts || data.alerts.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>Inventory Alerts</h2>
        </div>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>✅</div>
          <p>No inventory alerts at this time</p>
          <p style={{ fontSize: '14px', marginTop: '8px' }}>
            All inventory levels are within optimal ranges
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>
          Inventory Alerts ({filteredAlerts.length})
        </h2>
        <div className={styles.filterButtons}>
          <button
            className={`${styles.filterButton} ${filter === 'all' ? styles.active : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({data.alerts.length})
          </button>
          <button
            className={`${styles.filterButton} ${filter === 'critical' ? styles.active : ''}`}
            onClick={() => setFilter('critical')}
          >
            Critical ({priorityCounts.critical})
          </button>
          <button
            className={`${styles.filterButton} ${filter === 'warning' ? styles.active : ''}`}
            onClick={() => setFilter('warning')}
          >
            Warning ({priorityCounts.warning})
          </button>
          <button
            className={`${styles.filterButton} ${filter === 'info' ? styles.active : ''}`}
            onClick={() => setFilter('info')}
          >
            Info ({priorityCounts.info})
          </button>
        </div>
      </div>

      <div className={styles.alertsList}>
        {filteredAlerts.map((alert) => (
          <div key={alert.id} className={`${styles.alertCard} ${styles[alert.priority]}`}>
            <div className={styles.alertHeader}>
              <h3 className={styles.alertTitle}>
                {getPriorityIcon(alert.priority)} {alert.title}
              </h3>
              <span className={`${styles.alertPriority} ${styles[alert.priority]}`}>
                {alert.priority.toUpperCase()}
              </span>
            </div>

            <p className={styles.alertMessage}>{alert.message}</p>

            {alert.recommendation && (
              <div className={styles.alertRecommendation}>
                <div className={styles.recommendationLabel}>Recommended Action</div>
                <p className={styles.recommendationText}>{alert.recommendation}</p>
              </div>
            )}

            <div className={styles.alertFooter}>
              <div className={styles.alertMeta}>
                <span>Product: {alert.productName || alert.productId}</span>
                <span>•</span>
                <span>{formatDate(alert.createdAt)}</span>
                {alert.impact && (
                  <>
                    <span>•</span>
                    <span>Impact: {alert.impact}</span>
                  </>
                )}
              </div>
              <div className={styles.alertActions}>
                {alert.actionable && (
                  <button
                    className={styles.actionButton}
                    onClick={() => onTakeAction?.(alert.id)}
                  >
                    Take Action
                  </button>
                )}
                <button
                  className={`${styles.actionButton} ${styles.dismiss}`}
                  onClick={() => onDismiss?.(alert.id)}
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
