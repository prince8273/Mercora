import React from 'react';
import styles from './Skeleton.module.css';

export const Skeleton = ({ 
  width = '100%', 
  height = '1rem', 
  variant = 'text', // text, circular, rectangular
  className = '',
  ...props 
}) => {
  const style = {
    width,
    height: variant === 'circular' ? width : height,
  };

  return (
    <div 
      className={`${styles.skeleton} ${styles[variant]} ${className}`}
      style={style}
      {...props}
    />
  );
};
