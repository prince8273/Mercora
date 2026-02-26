import React from 'react';
import styles from './InsightCard.module.css';

export const InsightCard = ({
  title,
  description,
  value,
  change,
  trend,
  icon,
  variant = 'default', // 'default', 'success', 'warning', 'error'
  className = '',
  ...props
}) => {
  const getVariantClass = () => {
    return styles[`variant-${variant}`] || '';
  };

  const getTrendIcon = () => {
    if (!trend) return null;

    if (trend === 'up') {
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      );
    }

    if (trend === 'down') {
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
        </svg>
      );
    }

    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
      </svg>
    );
  };

  return (
    <div className={`${styles.container} ${getVariantClass()} ${className}`} {...props}>
      {icon && (
        <div className={styles.iconWrapper}>
          {icon}
        </div>
      )}

      <div className={styles.content}>
        <h4 className={styles.title}>{title}</h4>
        {description && (
          <p className={styles.description}>{description}</p>
        )}

        {value && (
          <div className={styles.valueRow}>
            <span className={styles.value}>{value}</span>
            {change && (
              <span className={`${styles.change} ${styles[`trend-${trend}`]}`}>
                <span className={styles.trendIcon}>{getTrendIcon()}</span>
                {change}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
