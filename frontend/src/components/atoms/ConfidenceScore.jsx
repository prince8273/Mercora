import React from 'react';
import { Tooltip } from './Tooltip';
import styles from './ConfidenceScore.module.css';

export const ConfidenceScore = ({
  score,
  size = 'md',
  showLabel = true,
  tooltip = null,
  className = '',
  ...props
}) => {
  // Normalize score to 0-100 range
  const normalizedScore = score > 1 ? score : score * 100;
  const roundedScore = Math.round(normalizedScore);

  // Determine confidence level and color
  const getConfidenceLevel = (score) => {
    if (score >= 80) return { level: 'high', color: 'green', label: 'High Confidence' };
    if (score >= 50) return { level: 'medium', color: 'yellow', label: 'Medium Confidence' };
    return { level: 'low', color: 'red', label: 'Low Confidence' };
  };

  const { level, color, label } = getConfidenceLevel(roundedScore);

  const defaultTooltip = tooltip || `AI is ${roundedScore}% confident in this prediction based on historical accuracy`;

  const badge = (
    <div
      className={`${styles.badge} ${styles[`badge-${color}`]} ${styles[`size-${size}`]} ${className}`}
      role="status"
      aria-label={`Confidence: ${roundedScore}%`}
      {...props}
    >
      <div className={styles.progressBar}>
        <div
          className={styles.progressFill}
          style={{ width: `${roundedScore}%` }}
          aria-hidden="true"
        />
      </div>
      <span className={styles.scoreText}>{roundedScore}%</span>
      {showLabel && size !== 'sm' && (
        <span className={styles.label}>{label}</span>
      )}
    </div>
  );

  return (
    <Tooltip content={defaultTooltip}>
      {badge}
    </Tooltip>
  );
};
