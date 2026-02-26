import { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { ChartContainer } from '../../../components/molecules/ChartContainer/ChartContainer';
import GaugeChart from './GaugeChart';
import styles from './SentimentOverview.module.css';

const SENTIMENT_COLORS = {
  positive: '#10b981',
  neutral: '#6b7280',
  negative: '#ef4444',
};

export default function SentimentOverview({ data, isLoading, timeRange, onTimeRangeChange }) {
  const distributionData = useMemo(() => {
    if (!data?.distribution) return [];
    
    return [
      { name: 'Positive', value: data.distribution.positive, color: SENTIMENT_COLORS.positive },
      { name: 'Neutral', value: data.distribution.neutral, color: SENTIMENT_COLORS.neutral },
      { name: 'Negative', value: data.distribution.negative, color: SENTIMENT_COLORS.negative },
    ];
  }, [data]);

  const sentimentScore = data?.overallScore || 0;
  const trend = data?.trend || 0;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Sentiment Overview</h2>
        <div className={styles.timeRangeSelector}>
          <button
            className={`${styles.timeButton} ${timeRange === '7d' ? styles.active : ''}`}
            onClick={() => onTimeRangeChange?.('7d')}
          >
            7 Days
          </button>
          <button
            className={`${styles.timeButton} ${timeRange === '30d' ? styles.active : ''}`}
            onClick={() => onTimeRangeChange?.('30d')}
          >
            30 Days
          </button>
          <button
            className={`${styles.timeButton} ${timeRange === '90d' ? styles.active : ''}`}
            onClick={() => onTimeRangeChange?.('90d')}
          >
            90 Days
          </button>
        </div>
      </div>

      <div className={styles.content}>
        {/* Overall Sentiment Gauge */}
        <div className={styles.gaugeSection}>
          <h3 className={styles.sectionTitle}>Overall Sentiment</h3>
          <GaugeChart value={sentimentScore} isLoading={isLoading} />
          <div className={styles.trendIndicator}>
            <span className={`${styles.trend} ${trend >= 0 ? styles.positive : styles.negative}`}>
              {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}%
            </span>
            <span className={styles.trendLabel}>vs previous period</span>
          </div>
        </div>

        {/* Distribution Chart */}
        <div className={styles.distributionSection}>
          <h3 className={styles.sectionTitle}>Sentiment Distribution</h3>
          <ChartContainer isLoading={isLoading} height={300}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={distributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {distributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>
      </div>

      {/* Summary Stats */}
      <div className={styles.stats}>
        <div className={styles.statCard}>
          <div className={styles.statValue} style={{ color: SENTIMENT_COLORS.positive }}>
            {data?.distribution?.positive || 0}%
          </div>
          <div className={styles.statLabel}>Positive</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statValue} style={{ color: SENTIMENT_COLORS.neutral }}>
            {data?.distribution?.neutral || 0}%
          </div>
          <div className={styles.statLabel}>Neutral</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statValue} style={{ color: SENTIMENT_COLORS.negative }}>
            {data?.distribution?.negative || 0}%
          </div>
          <div className={styles.statLabel}>Negative</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statValue}>{data?.totalReviews || 0}</div>
          <div className={styles.statLabel}>Total Reviews</div>
        </div>
      </div>
    </div>
  );
}
