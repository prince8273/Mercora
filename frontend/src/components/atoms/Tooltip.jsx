import React, { useState } from 'react';
import styles from './Tooltip.module.css';

export const Tooltip = ({ 
  children, 
  content, 
  position = 'top', // top, bottom, left, right
  delay = 200,
  className = '',
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [timeoutId, setTimeoutId] = useState(null);

  const showTooltip = () => {
    const id = setTimeout(() => {
      setIsVisible(true);
    }, delay);
    setTimeoutId(id);
  };

  const hideTooltip = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    setIsVisible(false);
  };

  if (!content) {
    return children;
  }

  return (
    <div 
      className={`${styles.tooltipWrapper} ${className}`}
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
    >
      {children}
      {isVisible && (
        <div className={`${styles.tooltip} ${styles[position]}`}>
          {content}
          <div className={styles.arrow} />
        </div>
      )}
    </div>
  );
};
