import React from 'react';
import { Button } from '../../../components/atoms/Button';
import { ConfidenceScore } from '../../../components/atoms/ConfidenceScore';
import { ImpactMetrics } from '../../../components/molecules/ImpactMetrics';
import { formatPrice } from '../../../utils/currency';
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
    type,
    title,
    current_price: currentPrice,
    suggested_price: suggestedPrice,
    profit_margin: profitMargin,
    expected_impact: expectedImpact,
    confidence,
    reasoning,
  } = recommendation;

  const priceChange = suggestedPrice - currentPrice;
  const priceChangePercent = ((priceChange / currentPrice) * 100).toFixed(1);

  const getTypeClass = () => {
    switch (type) {
      case 'competitive': return styles.typeCompetitive;
      case 'premium': return styles.typePremium;
      case 'optimization': return styles.typeOptimization;
      case 'opportunity': return styles.typeOpportunity;
      case 'dynamic': return styles.typeDynamic;
      default: return styles.typeDefault;
    }
  };

  const getTypeIcon = () => {
    switch (type) {
      case 'competitive':
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case 'premium':
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3l14 9-14 9V3z" />
          </svg>
        );
      case 'optimization':
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        );
      case 'opportunity':
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        );
      case 'dynamic':
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      default:
        return (
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const formatPriceValue = (price) => {
    return formatPrice(price); // Use centralized currency utility
  };

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <div className={styles.typeIndicator}>
          <div className={`${styles.typeIcon} ${getTypeClass()}`}>
            {getTypeIcon()}
          </div>
          <div className={styles.titleSection}>
            <h4 className={styles.title}>{title}</h4>
            <span className={`${styles.typeLabel} ${getTypeClass()}`}>
              {type.replace('_', ' ').toUpperCase()}
            </span>
          </div>
        </div>
        {confidence && (
          <div className={styles.confidenceSection}>
            <span className={styles.confidenceLabel}>Confidence</span>
            <span className={styles.confidenceValue}>{(confidence * 100).toFixed(0)}%</span>
          </div>
        )}
      </div>

      <div className={styles.priceComparison}>
        <div className={styles.priceItem}>
          <span className={styles.priceLabel}>Current Price</span>
          <span className={styles.currentPrice}>{formatPriceValue(currentPrice)}</span>
        </div>
        <div className={styles.arrow}>
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </div>
        <div className={styles.priceItem}>
          <span className={styles.priceLabel}>Suggested Price</span>
          <span className={styles.suggestedPrice}>{formatPriceValue(suggestedPrice)}</span>
        </div>
        <div className={styles.priceChange}>
          <span className={`${styles.changeValue} ${priceChange > 0 ? styles.increase : styles.decrease}`}>
            {priceChange > 0 ? '+' : ''}{priceChangePercent}%
          </span>
          {profitMargin && (
            <span className={styles.marginInfo}>
              {profitMargin}% margin
            </span>
          )}
        </div>
      </div>

      {expectedImpact && (
        <div className={styles.impactSection}>
          <h5 className={styles.impactTitle}>Expected Impact</h5>
          <div className={styles.impactMetrics}>
            {Object.entries(expectedImpact).map(([key, value]) => (
              <div key={key} className={styles.impactItem}>
                <span className={styles.impactLabel}>
                  {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                </span>
                <span className={styles.impactValue}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {reasoning && (
        <div className={styles.reasoning}>
          <h5 className={styles.reasoningTitle}>Analysis</h5>
          <p className={styles.reasoningText}>{reasoning}</p>
        </div>
      )}

      <div className={styles.actions}>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onReject?.(id)}
          disabled={loading}
        >
          Dismiss
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={() => onAccept?.(recommendation)}
          isLoading={loading}
        >
          Apply Pricing
        </Button>
      </div>
    </div>
  );
};
