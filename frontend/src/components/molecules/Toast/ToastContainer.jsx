import React from 'react';
import { Toast } from './Toast';
import styles from './ToastContainer.module.css';

export const ToastContainer = ({ toasts = [], onRemove }) => {
  if (toasts.length === 0) return null;

  return (
    <div className={styles.container}>
      {toasts.slice(0, 3).map((toast) => (
        <Toast
          key={toast.id}
          type={toast.type}
          title={toast.title}
          message={toast.message}
          duration={toast.duration}
          onClose={() => onRemove(toast.id)}
        />
      ))}
    </div>
  );
};
