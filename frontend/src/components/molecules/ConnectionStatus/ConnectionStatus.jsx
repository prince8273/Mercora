import React, { useEffect, useState } from 'react';
import { wsManager } from '../../../lib/websocket';
import styles from './ConnectionStatus.module.css';

export const ConnectionStatus = () => {
  const [status, setStatus] = useState('disconnected');
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const unsubscribe = wsManager.onStatusChange((newStatus) => {
      setStatus(newStatus);
      
      // Show banner if connection failed
      if (newStatus === 'failed') {
        setShowBanner(true);
      } else if (newStatus === 'connected') {
        setShowBanner(false);
      }
    });

    return unsubscribe;
  }, []);

  if (!showBanner) {
    return null;
  }

  return (
    <div className={styles.banner}>
      <div className={styles.content}>
        <svg
          className={styles.icon}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <div className={styles.text}>
          <strong>Real-time updates unavailable.</strong>
          <span> Using polling mode. Some features may have delayed updates.</span>
        </div>
        <button
          className={styles.closeButton}
          onClick={() => setShowBanner(false)}
          aria-label="Dismiss"
        >
          <svg
            width="20"
            height="20"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  );
};
