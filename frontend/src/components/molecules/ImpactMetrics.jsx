import React from 'react';
import styles from './ImpactMetrics.module.css';

export const ImpactMetrics = ({
  metrics = {},
  layout = 'horizontal',
  showChange = true,
  showTimeframe = true,
  className = '',
  ...props
}) => {
  const { revenue, margin, units, risk } = metrics;

  const formatCurrency = (value) => {
    if (!value) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value) => {
    if (!value) return '0';
    return new Intl.NumberFormat('en-US').format(value);
  };

  const formatPercentage = (value) => {
    if (!value) return '0%';
    return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  const getChangeIcon = (change) => {
    if (!change || change === 0) return null;
    if (change > 0) {
      return (
        <svg className={styles.iconUp} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
        </svg>
      );
    }
    return (
      <svg className={styles.iconDown} viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
    );
  };

  const getRiskColor = (level) => {
    const colors = {
      low: 'green',
      medium: 'yellow',
      high: 'red',
    };
    return colors[level?.toLowerCase()] || 'gray';
  };

  const renderMetric = (icon, label, value, change, timeframe, type = 'default') => {
    if (!value && value !== 0) return null;

    return (
      <div className={styles.metric} key={label}>
        <div className={styles.metricHeader}>
          <div className={styles.iconWrapper}>{icon}</div>
          <span className={styles.metricLabel}>{label}</span>
        </div>
        <div className={styles.metricValue}>
          <span className={styles.value}>{value}</span>
          {showChange && change && (
            <span className={`${styles.change} ${change > 0 ? styles.positive : styles.negative}`}>
              {getChangeIcon(change)}
              {type === 'percentage' ? formatPercentage(change) : `${change > 0 ? '+' : ''}${change}`}
            </span>
          )}
        </div>
        {showTimeframe && timeframe && (
          <span className={styles.timeframe}>{timeframe}</span>
        )}
      </div>
    );
  };

  return (
    <div className={`${styles.container} ${styles[`layout-${layout}`]} ${className}`} {...props}>
      {revenue && renderMetric(
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" />
        </svg>,
        'Revenue Impact',
        formatCurrency(revenue.value),
        revenue.change,
        revenue.timeframe,
        'currency'
      )}

      {margin && renderMetric(
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11 4a1 1 0 10-2 0v4a1 1 0 102 0V7zm-3 1a1 1 0 10-2 0v3a1 1 0 102 0V8zM8 9a1 1 0 00-2 0v2a1 1 0 102 0V9z" clipRule="evenodd" />
        </svg>,
        'Margin Impact',
        `${margin.value}%`,
        margin.change,
        null,
        'percentage'
      )}

      {units && renderMetric(
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 2a4 4 0 00-4 4v1H5a1 1 0 00-.994.89l-1 9A1 1 0 004 18h12a1 1 0 00.994-1.11l-1-9A1 1 0 0015 7h-1V6a4 4 0 00-4-4zm2 5V6a2 2 0 10-4 0v1h4zm-6 3a1 1 0 112 0 1 1 0 01-2 0zm7-1a1 1 0 100 2 1 1 0 000-2z" clipRule="evenodd" />
        </svg>,
        'Units Impact',
        formatNumber(units.value),
        units.change,
        null,
        'number'
      )}

      {risk && (
        <div className={styles.metric} key="risk">
          <div className={styles.metricHeader}>
            <div className={styles.iconWrapper}>
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <span className={styles.metricLabel}>Risk Level</span>
          </div>
          <div className={styles.metricValue}>
            <span className={`${styles.riskBadge} ${styles[`risk-${getRiskColor(risk.level)}`]}`}>
              {risk.level}
            </span>
          </div>
          {risk.description && (
            <span className={styles.riskDescription}>{risk.description}</span>
          )}
        </div>
      )}
    </div>
  );
};
