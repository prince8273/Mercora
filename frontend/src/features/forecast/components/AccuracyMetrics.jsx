import { useMemo } from 'react';
import { MetricCard } from '../../../components/molecules/MetricCard/MetricCard';
import styles from './AccuracyMetrics.module.css';

export default function AccuracyMetrics({ data, isLoading }) {
  const performanceRating = useMemo(() => {
    if (!data?.mape) return 'poor';

    const mape = data.mape;
    if (mape < 10) return 'excellent';
    if (mape < 20) return 'good';
    if (mape < 30) return 'fair';
    return 'poor';
  }, [data]);

  const performanceLabel = useMemo(() => {
    switch (performanceRating) {
      case 'excellent':
        return 'Excellent Accuracy';
      case 'good':
        return 'Good Accuracy';
      case 'fair':
        return 'Fair Accuracy';
      case 'poor':
        return 'Poor Accuracy';
      default:
        return 'Unknown';
    }
  }, [performanceRating]);

  const performanceIcon = useMemo(() => {
    switch (performanceRating) {
      case 'excellent':
        return '🎯';
      case 'good':
        return '✅';
      case 'fair':
        return '⚠️';
      case 'poor':
        return '❌';
      default:
        return '📊';
    }
  }, [performanceRating]);

  const comparisonData = useMemo(() => {
    if (!data) return [];

    return [
      {
        name: 'Current Model',
        value: data.mape || 0,
        color: '#3b82f6',
      },
      {
        name: 'Baseline Model',
        value: data.baselineMape || 0,
        color: '#6b7280',
      },
      {
        name: 'Industry Average',
        value: data.industryAverage || 25,
        color: '#f59e0b',
      },
    ];
  }, [data]);

  if (!data) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>Forecast Accuracy Metrics</h2>
        </div>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>📊</div>
          <p>No accuracy metrics available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Forecast Accuracy Metrics</h2>
        <p className={styles.subtitle}>
          Measuring the precision of demand forecasts against actual outcomes
        </p>
      </div>

      <div className={styles.metricsGrid}>
        {/* MAPE */}
        <div className={styles.metricCard}>
          <div className={styles.metricHeader}>
            <div className={styles.metricLabel}>MAPE</div>
            <div className={styles.metricInfo} title="Mean Absolute Percentage Error">
              ?
            </div>
          </div>
          <div className={`${styles.metricValue} ${styles[performanceRating]}`}>
            {data.mape?.toFixed(1)}%
          </div>
          <div className={styles.metricDescription}>
            Average percentage difference between forecast and actual values. Lower is better.
          </div>
          {data.mapeTrend && (
            <div
              className={`${styles.metricTrend} ${
                data.mapeTrend < 0 ? styles.improving : styles.declining
              }`}
            >
              {data.mapeTrend < 0 ? '↓' : '↑'} {Math.abs(data.mapeTrend).toFixed(1)}% vs last
              period
            </div>
          )}
        </div>

        {/* RMSE */}
        <div className={styles.metricCard}>
          <div className={styles.metricHeader}>
            <div className={styles.metricLabel}>RMSE</div>
            <div className={styles.metricInfo} title="Root Mean Square Error">
              ?
            </div>
          </div>
          <div className={styles.metricValue}>{data.rmse?.toFixed(0)}</div>
          <div className={styles.metricDescription}>
            Standard deviation of forecast errors. Penalizes large errors more heavily.
          </div>
          {data.rmseTrend && (
            <div
              className={`${styles.metricTrend} ${
                data.rmseTrend < 0 ? styles.improving : styles.declining
              }`}
            >
              {data.rmseTrend < 0 ? '↓' : '↑'} {Math.abs(data.rmseTrend).toFixed(1)}% vs last
              period
            </div>
          )}
        </div>

        {/* MAE */}
        <div className={styles.metricCard}>
          <div className={styles.metricHeader}>
            <div className={styles.metricLabel}>MAE</div>
            <div className={styles.metricInfo} title="Mean Absolute Error">
              ?
            </div>
          </div>
          <div className={styles.metricValue}>{data.mae?.toFixed(0)}</div>
          <div className={styles.metricDescription}>
            Average absolute difference between forecast and actual values.
          </div>
          {data.maeTrend && (
            <div
              className={`${styles.metricTrend} ${
                data.maeTrend < 0 ? styles.improving : styles.declining
              }`}
            >
              {data.maeTrend < 0 ? '↓' : '↑'} {Math.abs(data.maeTrend).toFixed(1)}% vs last period
            </div>
          )}
        </div>

        {/* R-Squared */}
        <div className={styles.metricCard}>
          <div className={styles.metricHeader}>
            <div className={styles.metricLabel}>R²</div>
            <div className={styles.metricInfo} title="Coefficient of Determination">
              ?
            </div>
          </div>
          <div className={styles.metricValue}>
            {data.rSquared ? (data.rSquared * 100).toFixed(1) : 0}%
          </div>
          <div className={styles.metricDescription}>
            Proportion of variance explained by the model. Higher is better (max 100%).
          </div>
        </div>
      </div>

      {/* Performance Indicator */}
      <div className={`${styles.performanceIndicator} ${styles[performanceRating]}`}>
        <div className={styles.performanceIcon}>{performanceIcon}</div>
        <div className={styles.performanceText}>
          <div className={styles.performanceLabel}>Overall Performance</div>
          <div className={styles.performanceStatus}>{performanceLabel}</div>
        </div>
      </div>

      {/* Comparison Section */}
      <div className={styles.comparisonSection}>
        <h3 className={styles.comparisonTitle}>MAPE Comparison</h3>
        <div className={styles.comparisonBars}>
          {comparisonData.map((item, index) => (
            <div key={index} className={styles.comparisonItem}>
              <div className={styles.comparisonLabel}>
                <span className={styles.comparisonName}>{item.name}</span>
                <span className={styles.comparisonValue}>{item.value.toFixed(1)}%</span>
              </div>
              <div className={styles.comparisonBar}>
                <div
                  className={styles.comparisonBarFill}
                  style={{
                    width: `${Math.min((item.value / 50) * 100, 100)}%`,
                    background: item.color,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
