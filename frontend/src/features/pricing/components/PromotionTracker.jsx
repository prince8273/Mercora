import React from 'react';
import { MetricCard } from '../../../components/molecules/MetricCard';
import { StatusIndicator } from '../../../components/molecules/StatusIndicator';
import { LoadingSkeleton } from '../../../components/molecules/LoadingSkeleton';
import styles from './PromotionTracker.module.css';

export const PromotionTracker = ({
  promotions = [],
  loading = false,
  error = null,
  className = '',
  ...props
}) => {
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value) => `${value.toFixed(1)}%`;

  const getStatusType = (status) => {
    const statusMap = {
      active: 'active',
      scheduled: 'idle',
      ended: 'error',
    };
    return statusMap[status] || 'idle';
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Promotion Tracker</h3>
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
          <h3 className={styles.title}>Promotion Tracker</h3>
        </div>
        <div className={styles.errorState}>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!promotions || promotions.length === 0) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Promotion Tracker</h3>
        </div>
        <div className={styles.emptyState}>
          <svg className={styles.emptyIcon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className={styles.emptyText}>No active promotions</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <h3 className={styles.title}>
          Promotion Tracker
          <span className={styles.count}>({promotions.length})</span>
        </h3>
      </div>

      <div className={styles.content}>
        {promotions.map((promotion) => (
          <div key={promotion.id} className={styles.promotionCard}>
            <div className={styles.promotionHeader}>
              <div className={styles.promotionInfo}>
                <h4 className={styles.promotionName}>{promotion.name}</h4>
                <div className={styles.promotionMeta}>
                  <StatusIndicator
                    status={getStatusType(promotion.status)}
                    label={promotion.status}
                    size="sm"
                  />
                  <span className={styles.promotionDates}>
                    {formatDate(promotion.startDate)} - {formatDate(promotion.endDate)}
                  </span>
                </div>
              </div>
              <div className={styles.promotionDiscount}>
                <span className={styles.discountValue}>{promotion.discount}%</span>
                <span className={styles.discountLabel}>OFF</span>
              </div>
            </div>

            {promotion.metrics && (
              <div className={styles.metricsGrid}>
                <div className={styles.metricItem}>
                  <span className={styles.metricLabel}>Sales Lift</span>
                  <span className={`${styles.metricValue} ${promotion.metrics.salesLift > 0 ? styles.positive : ''}`}>
                    {promotion.metrics.salesLift > 0 ? '+' : ''}{formatPercentage(promotion.metrics.salesLift)}
                  </span>
                </div>
                <div className={styles.metricItem}>
                  <span className={styles.metricLabel}>Revenue</span>
                  <span className={styles.metricValue}>
                    {formatCurrency(promotion.metrics.revenue)}
                  </span>
                </div>
                <div className={styles.metricItem}>
                  <span className={styles.metricLabel}>ROI</span>
                  <span className={`${styles.metricValue} ${promotion.metrics.roi > 0 ? styles.positive : styles.negative}`}>
                    {formatPercentage(promotion.metrics.roi)}
                  </span>
                </div>
                <div className={styles.metricItem}>
                  <span className={styles.metricLabel}>Units Sold</span>
                  <span className={styles.metricValue}>
                    {promotion.metrics.unitsSold.toLocaleString()}
                  </span>
                </div>
              </div>
            )}

            {promotion.products && promotion.products.length > 0 && (
              <div className={styles.products}>
                <span className={styles.productsLabel}>Products:</span>
                <span className={styles.productsCount}>
                  {promotion.products.length} {promotion.products.length === 1 ? 'product' : 'products'}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
