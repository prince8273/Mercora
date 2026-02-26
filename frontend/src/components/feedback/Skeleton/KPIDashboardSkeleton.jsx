import React from 'react';
import { LoadingSkeleton } from '../../molecules/LoadingSkeleton';
import styles from './KPIDashboardSkeleton.module.css';

export const KPIDashboardSkeleton = () => {
  return (
    <div className={styles.container}>
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className={styles.card}>
          <LoadingSkeleton width="60%" height="1rem" style={{ marginBottom: '0.5rem' }} />
          <LoadingSkeleton width="80%" height="2rem" style={{ marginBottom: '0.5rem' }} />
          <LoadingSkeleton width="40%" height="0.875rem" />
        </div>
      ))}
    </div>
  );
};
