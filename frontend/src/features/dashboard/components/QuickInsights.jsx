import React, { useState } from 'react';
import { LoadingSkeleton } from '../../../components/molecules/LoadingSkeleton';
import { ConfidenceScore } from '../../../components/atoms/ConfidenceScore';
import { ActionRecommendation } from '../../../components/molecules/ActionRecommendation';
import styles from './QuickInsights.module.css';

export const QuickInsights = ({
  insights = [],
  loading = false,
  onAcceptAction,
  onSnoozeAction,
  onRejectAction,
  className = '',
  ...props
}) => {
  const [expandedInsight, setExpandedInsight] = useState(null);

  const handleToggle = (insightId) => {
    setExpandedInsight(expandedInsight === insightId ? null : insightId);
  };

  const getInsightIcon = (type) => {
    const icons = {
      trend: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      ),
      warning: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
      opportunity: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      ),
      alert: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      ),
      success: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      info: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    };
    return icons[type] || icons.info;
  };

  if (loading) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Quick Insights</h3>
        </div>
        <div className={styles.content}>
          <LoadingSkeleton variant="list" count={4} />
        </div>
      </div>
    );
  }

  if (!insights || insights.length === 0) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Quick Insights</h3>
        </div>
        <div className={styles.content}>
          <div className={styles.emptyState}>
            <svg
              className={styles.emptyIcon}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            <p className={styles.emptyText}>No insights available</p>
            <p className={styles.emptySubtext}>
              Check back later for AI-generated insights about your business.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <h3 className={styles.title}>Quick Insights</h3>
        <span className={styles.badge}>{insights.length}</span>
      </div>
      <div className={styles.content}>
        <ul className={styles.insightList} role="list">
          {insights.map((insight) => (
            <li key={insight.id} className={styles.insightItem}>
              <button
                className={styles.insightButton}
                onClick={() => handleToggle(insight.id)}
                aria-expanded={expandedInsight === insight.id}
              >
                <div className={styles.insightHeader}>
                  <div className={`${styles.iconWrapper} ${styles[`icon-${insight.type}`]}`}>
                    {getInsightIcon(insight.type)}
                  </div>
                  <div className={styles.insightContent}>
                    <h4 className={styles.insightTitle}>{insight.title}</h4>
                    <p className={styles.insightSummary}>{insight.summary}</p>
                  </div>
                  <svg
                    className={`${styles.expandIcon} ${
                      expandedInsight === insight.id ? styles.expanded : ''
                    }`}
                    width="20"
                    height="20"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
              </button>

              {expandedInsight === insight.id && insight.details && (
                <div className={styles.insightDetails}>
                  <p className={styles.detailsText}>{insight.details}</p>
                  {insight.metrics && insight.metrics.length > 0 && (
                    <div className={styles.metrics}>
                      {insight.metrics.map((metric, index) => (
                        <div key={index} className={styles.metric}>
                          <span className={styles.metricLabel}>{metric.label}:</span>
                          <span className={styles.metricValue}>{metric.value}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {insight.confidence && (
                    <div className={styles.confidenceWrapper}>
                      <ConfidenceScore 
                        score={insight.confidence} 
                        size="sm" 
                        showLabel={true}
                      />
                    </div>
                  )}
                  {insight.action && (
                    <ActionRecommendation
                      action={insight.action}
                      onAccept={onAcceptAction}
                      onSnooze={onSnoozeAction}
                      onReject={onRejectAction}
                    />
                  )}
                  {!insight.action && insight.recommendation && (
                    <div className={styles.recommendation}>
                      <strong>Recommendation:</strong> {insight.recommendation}
                    </div>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
