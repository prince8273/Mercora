import React from 'react';
import { Skeleton } from '../../atoms/Skeleton';
import styles from './ChartContainer.module.css';

export const ChartContainer = ({
  children,
  title,
  loading = false,
  error,
  height = 400,
  showLegend = true,
  className = '',
  ...props
}) => {
  if (loading) {
    return (
      <div className={`${styles.container} ${className}`} style={{ height }} {...props}>
        {title && (
          <div className={styles.header}>
            <Skeleton width="40%" height="1.5rem" />
          </div>
        )}
        <div className={styles.chartArea}>
          <Skeleton width="100%" height={height - 80} variant="rectangular" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${styles.container} ${className}`} style={{ height }} {...props}>
        {title && (
          <div className={styles.header}>
            <h3 className={styles.title}>{title}</h3>
          </div>
        )}
        <div className={styles.errorState}>
          <svg className={styles.errorIcon} viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <p className={styles.errorMessage}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      {title && (
        <div className={styles.header}>
          <h3 className={styles.title}>{title}</h3>
        </div>
      )}
      <div className={styles.chartArea} style={{ height }}>
        {children}
      </div>
    </div>
  );
};
