import React from 'react';
import { Skeleton } from '../../atoms/Skeleton';
import styles from './LoadingSkeleton.module.css';

export const LoadingSkeleton = ({
  variant = 'card', // 'card', 'table', 'chart', 'text', 'avatar', 'list'
  count = 1,
  className = '',
  ...props
}) => {
  const renderSkeleton = () => {
    switch (variant) {
      case 'card':
        return (
          <div className={styles.card}>
            <Skeleton width="100%" height="200px" variant="rectangular" />
            <div className={styles.cardContent}>
              <Skeleton width="60%" height="1.5rem" />
              <Skeleton width="100%" height="1rem" />
              <Skeleton width="80%" height="1rem" />
            </div>
          </div>
        );

      case 'table':
        return (
          <div className={styles.table}>
            <div className={styles.tableHeader}>
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} width="100%" height="1rem" />
              ))}
            </div>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className={styles.tableRow}>
                {Array.from({ length: 4 }).map((_, j) => (
                  <Skeleton key={j} width="90%" height="1rem" />
                ))}
              </div>
            ))}
          </div>
        );

      case 'chart':
        return (
          <div className={styles.chart}>
            <Skeleton width="40%" height="1.5rem" />
            <Skeleton width="100%" height="300px" variant="rectangular" />
          </div>
        );

      case 'text':
        return (
          <div className={styles.text}>
            <Skeleton width="100%" height="1rem" />
            <Skeleton width="95%" height="1rem" />
            <Skeleton width="90%" height="1rem" />
          </div>
        );

      case 'avatar':
        return (
          <div className={styles.avatar}>
            <Skeleton width="3rem" height="3rem" variant="circular" />
            <div className={styles.avatarText}>
              <Skeleton width="120px" height="1rem" />
              <Skeleton width="80px" height="0.875rem" />
            </div>
          </div>
        );

      case 'list':
        return (
          <div className={styles.list}>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className={styles.listItem}>
                <Skeleton width="2rem" height="2rem" variant="circular" />
                <div className={styles.listContent}>
                  <Skeleton width="60%" height="1rem" />
                  <Skeleton width="40%" height="0.875rem" />
                </div>
              </div>
            ))}
          </div>
        );

      default:
        return <Skeleton width="100%" height="1rem" />;
    }
  };

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i}>{renderSkeleton()}</div>
      ))}
    </div>
  );
};
