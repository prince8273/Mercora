import React from 'react';
import { LoadingSkeleton } from '../../molecules/LoadingSkeleton';
import styles from './ChartSkeleton.module.css';

export const ChartSkeleton = ({ height = '300px' }) => {
  return (
    <div className={styles.container} style={{ height }}>
      {/* Chart Title */}
      <div className={styles.header}>
        <LoadingSkeleton width="40%" height="1.25rem" />
        <LoadingSkeleton width="20%" height="1rem" />
      </div>
      
      {/* Chart Area */}
      <div className={styles.chartArea}>
        {/* Y-axis labels */}
        <div className={styles.yAxis}>
          {[1, 2, 3, 4, 5].map((i) => (
            <LoadingSkeleton key={i} width="2rem" height="0.75rem" />
          ))}
        </div>
        
        {/* Chart bars/lines */}
        <div className={styles.chart}>
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <div key={i} className={styles.bar}>
              <LoadingSkeleton 
                width="100%" 
                height={`${Math.random() * 60 + 40}%`}
                style={{ borderRadius: '0.25rem 0.25rem 0 0' }}
              />
            </div>
          ))}
        </div>
      </div>
      
      {/* X-axis labels */}
      <div className={styles.xAxis}>
        {[1, 2, 3, 4, 5, 6, 7].map((i) => (
          <LoadingSkeleton key={i} width="3rem" height="0.75rem" />
        ))}
      </div>
      
      {/* Legend */}
      <div className={styles.legend}>
        {[1, 2, 3].map((i) => (
          <div key={i} className={styles.legendItem}>
            <LoadingSkeleton width="1rem" height="1rem" style={{ borderRadius: '0.125rem' }} />
            <LoadingSkeleton width="4rem" height="0.875rem" />
          </div>
        ))}
      </div>
    </div>
  );
};
