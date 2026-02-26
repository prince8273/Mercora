import React from 'react';
import { Tooltip } from '../../atoms/Tooltip';
import styles from './StatusIndicator.module.css';

export const StatusIndicator = ({
  status = 'idle', // 'active', 'idle', 'success', 'warning', 'error'
  label,
  pulse = false,
  tooltip,
  size = 'md', // 'sm', 'md', 'lg'
  className = '',
  ...props
}) => {
  const indicator = (
    <div className={`${styles.container} ${className}`} {...props}>
      <span
        className={`${styles.dot} ${styles[status]} ${styles[size]} ${
          pulse ? styles.pulse : ''
        }`}
        aria-label={tooltip || label || status}
      />
      {label && <span className={styles.label}>{label}</span>}
    </div>
  );

  if (tooltip) {
    return <Tooltip content={tooltip}>{indicator}</Tooltip>;
  }

  return indicator;
};
