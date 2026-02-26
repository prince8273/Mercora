import React, { useState } from 'react';
import styles from './InsightCard.module.css';

export const InsightCard = ({
  title,
  description,
  value,
  change,
  trend,
  icon,
  variant = 'default', // 'default', 'success', 'warning', 'error'
  details = null, // Array of detailed items to show when expanded
  className = '',
  ...props
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getVariantClass = () => {
    return styles[`variant-${variant}`] || '';
  };

  const getTrendIcon = () => {
    if (!trend) return null;

    if (trend === 'up') {
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      );
    }

    if (trend === 'down') {
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
        </svg>
      );
    }

    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
      </svg>
    );
  };

  const hasDetails = details && details.length > 0;

  return (
    <div className={`${styles.container} ${getVariantClass()} ${className}`} {...props}>
      {icon && (
        <div className={styles.iconWrapper}>
          {icon}
        </div>
      )}

      <div className={styles.content}>
        <h4 className={styles.title}>{title}</h4>
        {description && (
          <p className={styles.description}>{description}</p>
        )}

        {value && (
          <div className={styles.valueRow}>
            <span className={styles.value}>{value}</span>
            {change && (
              <span className={`${styles.change} ${styles[`trend-${trend}`]}`}>
                <span className={styles.trendIcon}>{getTrendIcon()}</span>
                {change}
              </span>
            )}
          </div>
        )}

        {/* Expandable details section */}
        {hasDetails && (
          <div className={styles.detailsSection}>
            <button
              className={styles.expandButton}
              onClick={() => setIsExpanded(!isExpanded)}
              aria-expanded={isExpanded}
            >
              <span>
                {isExpanded ? 'Hide' : 'Show'} {details.length} item{details.length !== 1 ? 's' : ''}
              </span>
              <svg
                className={`${styles.expandIcon} ${isExpanded ? styles.expanded : ''}`}
                width="16"
                height="16"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {isExpanded && (
              <div className={styles.detailsList}>
                {details.map((detail, index) => (
                  <div key={index} className={styles.detailItem}>
                    <div className={styles.detailHeader}>
                      <span className={styles.detailSku}>{detail.sku || detail.name}</span>
                      {detail.badge && (
                        <span className={`${styles.detailBadge} ${styles[`badge-${detail.badgeVariant || 'default'}`]}`}>
                          {detail.badge}
                        </span>
                      )}
                    </div>
                    {detail.name && detail.sku && (
                      <div className={styles.detailName}>{detail.name}</div>
                    )}
                    {detail.description && (
                      <div className={styles.detailDescription}>{detail.description}</div>
                    )}
                    {detail.metrics && (
                      <div className={styles.detailMetrics}>
                        {detail.metrics.map((metric, mIndex) => (
                          <span key={mIndex} className={styles.metric}>
                            <span className={styles.metricLabel}>{metric.label}:</span>
                            <span className={styles.metricValue}>{metric.value}</span>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
