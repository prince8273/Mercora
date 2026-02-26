import React from 'react';
import styles from './ExecutiveSummary.module.css';

export const ExecutiveSummary = ({
  summary = '',
  keyFindings = [],
  className = '',
  ...props
}) => {
  if (!summary && (!keyFindings || keyFindings.length === 0)) {
    return null;
  }

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <h3 className={styles.title}>Executive Summary</h3>

      {summary && (
        <p className={styles.summary}>{summary}</p>
      )}

      {keyFindings && keyFindings.length > 0 && (
        <div className={styles.findings}>
          <h4 className={styles.findingsTitle}>Key Findings</h4>
          <ul className={styles.findingsList}>
            {keyFindings.map((finding, index) => (
              <li key={index} className={styles.findingItem}>
                <svg
                  className={styles.findingIcon}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
