import React, { createContext, useContext, useState, useCallback } from 'react';
import { Toast } from '../../molecules/Toast';
import styles from './ToastManager.module.css';

const ToastContext = createContext(null);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);
  const maxVisible = 3;

  const addToast = useCallback((toast) => {
    const id = Date.now() + Math.random();
    const newToast = {
      id,
      type: toast.type || 'info',
      title: toast.title,
      message: toast.message,
      duration: toast.duration || 5000,
    };

    setToasts((prev) => {
      // If we have max visible toasts, queue the new one
      const visible = prev.filter((t) => !t.queued);
      if (visible.length >= maxVisible) {
        return [...prev, { ...newToast, queued: true }];
      }
      return [...prev, newToast];
    });

    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => {
      const filtered = prev.filter((t) => t.id !== id);
      
      // If there are queued toasts, show the next one
      const queued = filtered.find((t) => t.queued);
      if (queued) {
        return filtered.map((t) =>
          t.id === queued.id ? { ...t, queued: false } : t
        );
      }
      
      return filtered;
    });
  }, []);

  const success = useCallback(
    (title, message, duration) => {
      return addToast({ type: 'success', title, message, duration });
    },
    [addToast]
  );

  const error = useCallback(
    (title, message, duration) => {
      return addToast({ type: 'error', title, message, duration });
    },
    [addToast]
  );

  const warning = useCallback(
    (title, message, duration) => {
      return addToast({ type: 'warning', title, message, duration });
    },
    [addToast]
  );

  const info = useCallback(
    (title, message, duration) => {
      return addToast({ type: 'info', title, message, duration });
    },
    [addToast]
  );

  const value = {
    success,
    error,
    warning,
    info,
    addToast,
    removeToast,
  };

  const visibleToasts = toasts.filter((t) => !t.queued);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className={styles.toastContainer}>
        {visibleToasts.map((toast) => (
          <Toast
            key={toast.id}
            type={toast.type}
            title={toast.title}
            message={toast.message}
            duration={toast.duration}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};
