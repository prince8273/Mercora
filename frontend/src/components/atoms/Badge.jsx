import React from 'react';
import styles from './Badge.module.css';

export const Badge = ({ 
  children, 
  variant = 'default', // default, primary, success, warning, error, info
  size = 'md', // sm, md, lg
  className = '',
  ...props 
}) => {
  return (
    <span 
      className={`${styles.badge} ${styles[variant]} ${styles[size]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};
