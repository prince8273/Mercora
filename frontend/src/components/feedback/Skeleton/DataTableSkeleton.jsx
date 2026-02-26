import React from 'react';
import { LoadingSkeleton } from '../../molecules/LoadingSkeleton';
import styles from './DataTableSkeleton.module.css';

export const DataTableSkeleton = ({ rows = 5, columns = 4 }) => {
  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        {Array.from({ length: columns }).map((_, i) => (
          <div key={i} className={styles.headerCell}>
            <LoadingSkeleton width="70%" height="1rem" />
          </div>
        ))}
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className={styles.row}>
          {Array.from({ length: columns }).map((_, colIndex) => (
            <div key={colIndex} className={styles.cell}>
              <LoadingSkeleton width="85%" height="0.875rem" />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};
