import React from 'react';
import styles from './ProgressBar.module.css';

export const ProgressBar = ({
  value = 0,
  max = 100,
  variant = 'primary', // 'primary', 'success', 'warning', 'error'
  size = 'md', // 'sm', 'md', 'lg'
  showLabel = false,
  label,
  className = '',
  ...props
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      {(showLabel || label) && (
        <div className={styles.labelContainer}>
          {label && <span className={styles.label}>{label}</span>}
          {showLabel && (
            <span className={styles.percentage}>{Math.round(percentage)}%</span>
          )}
        </div>
      )}
      <div
        className={`${styles.track} ${styles[size]}`}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        <div
          className={`${styles.fill} ${styles[variant]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
