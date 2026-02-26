import React from 'react';
import { Skeleton } from '../../atoms/Skeleton';
import styles from './MetricCard.module.css';

export const MetricCard = ({ 
  title,
  value,
  change,
  trend = 'neutral', // 'up', 'down', 'neutral'
  loading = false,
  format = 'number', // 'currency', 'percentage', 'number'
  icon,
  className = '',
  ...props 
}) => {
  if (loading) {
    return (
      <div className={`${styles.card} ${className}`} {...props}>
        <div className={styles.header}>
          <Skeleton width="60%" height="1rem" />
        </div>
        <div className={styles.body}>
          <Skeleton width="80%" height="2rem" />
          <Skeleton width="40%" height="0.875rem" />
        </div>
      </div>
    );
  }

  const formatValue = (val) => {
    if (val === null || val === undefined) return '—';
    
    // Convert to number if it's a string
    const numVal = typeof val === 'string' ? parseFloat(val) : val;
    if (isNaN(numVal)) return '—';
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(numVal);
      
      case 'percentage':
        return `${numVal.toFixed(1)}%`;
      
      case 'number':
      default:
        return new Intl.NumberFormat('en-US').format(numVal);
    }
  };

  const formatChange = (val) => {
    if (val === null || val === undefined) return null;
    // Convert to number if it's a string
    const numVal = typeof val === 'string' ? parseFloat(val) : val;
    if (isNaN(numVal)) return null;
    const sign = numVal > 0 ? '+' : '';
    return `${sign}${numVal.toFixed(1)}%`;
  };

  const getTrendIcon = () => {
    if (trend === 'up') {
      return (
        <svg className={styles.trendIcon} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
        </svg>
      );
    }
    if (trend === 'down') {
      return (
        <svg className={styles.trendIcon} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      );
    }
    return null;
  };

  const trendClass = change !== null && change !== undefined
    ? (typeof change === 'string' ? parseFloat(change) : change) > 0 
      ? styles.positive 
      : (typeof change === 'string' ? parseFloat(change) : change) < 0 
        ? styles.negative 
        : styles.neutral
    : styles.neutral;

  return (
    <div className={`${styles.card} ${className}`} {...props}>
      <div className={styles.header}>
        {icon && <div className={styles.icon}>{icon}</div>}
        <h3 className={styles.title}>{title}</h3>
        {change !== null && change !== undefined && (
          <div className={`${styles.change} ${trendClass}`}>
            {getTrendIcon()}
            <span>{formatChange(change)}</span>
          </div>
        )}
      </div>
      <div className={styles.body}>
        <div className={styles.value}>{formatValue(value)}</div>
        {change !== null && change !== undefined && (
          <div className={styles.subtitle}>vs last period</div>
        )}
      </div>
    </div>
  );
};
