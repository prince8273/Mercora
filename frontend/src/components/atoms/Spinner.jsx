import React from 'react';
import styles from './Spinner.module.css';

export const Spinner = ({ 
  size = 'md', // sm, md, lg
  variant = 'primary', // primary, secondary, white
  className = '',
  ...props 
}) => {
  return (
    <div 
      className={`${styles.spinner} ${styles[size]} ${styles[variant]} ${className}`}
      role="status"
      aria-label="Loading"
      {...props}
    >
      <span className={styles.visuallyHidden}>Loading...</span>
    </div>
  );
};
