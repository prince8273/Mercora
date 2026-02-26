import React from 'react';
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';
import styles from './Alert.module.css';

const icons = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertCircle,
};

export const Alert = ({ 
  children, 
  variant = 'info', // info, success, warning, error
  title,
  onClose,
  className = '',
  ...props 
}) => {
  const Icon = icons[variant];

  return (
    <div 
      className={`${styles.alert} ${styles[variant]} ${className}`}
      role="alert"
      {...props}
    >
      <div className={styles.iconWrapper}>
        <Icon className={styles.icon} size={20} />
      </div>
      <div className={styles.content}>
        {title && <div className={styles.title}>{title}</div>}
        <div className={styles.message}>{children}</div>
      </div>
      {onClose && (
        <button 
          className={styles.closeButton}
          onClick={onClose}
          aria-label="Close alert"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};
