import React from 'react';
import { RecommendationCard } from './RecommendationCard';
import { LoadingSkeleton } from '../../../components/molecules/LoadingSkeleton';
import styles from './RecommendationPanel.module.css';

export const RecommendationPanel = ({
  recommendations = [],
  loading = false,
  error = null,
  onAccept,
  onReject,
  className = '',
  ...props
}) => {
  if (loading) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Pricing Recommendations</h3>
        </div>
        <div className={styles.content}>
          <LoadingSkeleton variant="card" count={3} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Pricing Recommendations</h3>
        </div>
        <div className={styles.errorState}>
          <svg className={styles.errorIcon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Pricing Recommendations</h3>
        </div>
        <div className={styles.emptyState}>
          <svg className={styles.emptyIcon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className={styles.emptyText}>No recommendations available</p>
          <p className={styles.emptySubtext}>
            Your current pricing is optimal based on market conditions.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <h3 className={styles.title}>
          Pricing Recommendations
          <span className={styles.count}>({recommendations.length})</span>
        </h3>
        <p className={styles.subtitle}>
          AI-powered pricing suggestions based on competitor analysis and market trends
        </p>
      </div>

      <div className={styles.content}>
        {recommendations.map((recommendation) => (
          <RecommendationCard
            key={recommendation.id}
            recommendation={recommendation}
            onAccept={onAccept}
            onReject={onReject}
          />
        ))}
      </div>
    </div>
  );
};
