import React from 'react';
import { Button } from '../../../components/atoms/Button';
import { ConfidenceScore } from '../../../components/atoms/ConfidenceScore';
import { ImpactMetrics } from '../../../components/molecules/ImpactMetrics';
import styles from './RecommendationCard.module.css';

export const RecommendationCard = ({
  recommendation,
  onAccept,
  onReject,
  loading = false,
  className = '',
  ...props
}) => {
  const {
    id,
    productName,
    currentPrice,
    recommendedPrice,
    confidence,
    expectedImpact,
    reasoning,
  } = recommendation;

  const priceChange = recommendedPrice - currentPrice;
  const priceChangePercent = ((priceChange / currentPrice) * 100).toFixed(1);

  const getConfidenceClass = () => {
    if (confidence >= 80) return styles.confidenceHigh;
    if (confidence >= 60) return styles.confidenceMedium;
    return styles.confidenceLow;
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(price);
  };

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <div className={styles.productInfo}>
          <h4 className={styles.productName}>{productName}</h4>
          <div className={styles.priceComparison}>
            <span className={styles.currentPrice}>{formatPrice(currentPrice)}</span>
            <svg className={styles.arrow} width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
            <span className={styles.recommendedPrice}>{formatPrice(recommendedPrice)}</span>
            <span className={`${styles.priceChange} ${priceChange > 0 ? styles.increase : styles.decrease}`}>
              {priceChange > 0 ? '+' : ''}{priceChangePercent}%
            </span>
          </div>
        </div>
        {confidence && (
          <ConfidenceScore score={confidence / 100} size="md" showLabel={true} />
        )}
      </div>

      {expectedImpact && (
        <ImpactMetrics
          metrics={{
            revenue: {
              value: expectedImpact.revenue,
              change: null,
              timeframe: '30 days'
            },
            margin: {
              value: expectedImpact.margin,
              change: null
            }
          }}
          layout="horizontal"
          showChange={false}
          showTimeframe={true}
        />
      )}

      {reasoning && (
        <div className={styles.reasoning}>
          <h5 className={styles.reasoningTitle}>Reasoning</h5>
          <p className={styles.reasoningText}>{reasoning}</p>
        </div>
      )}

      <div className={styles.actions}>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onReject(id)}
          disabled={loading}
        >
          Reject
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={() => onAccept(id)}
          loading={loading}
        >
          Accept & Apply
        </Button>
      </div>
    </div>
  );
};
