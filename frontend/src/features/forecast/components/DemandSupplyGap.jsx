import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { ChartContainer } from '../../../components/molecules/ChartContainer/ChartContainer';
import styles from './DemandSupplyGap.module.css';

export default function DemandSupplyGap({ data, isLoading, timeRange, onTimeRangeChange }) {
  const chartData = useMemo(() => {
    if (!data?.gaps) return [];

    return data.gaps.map((item) => ({
      ...item,
      gap: item.supply - item.demand,
      gapAbs: Math.abs(item.supply - item.demand),
    }));
  }, [data]);

  const summary = useMemo(() => {
    if (!chartData.length) return null;

    const totalSurplus = chartData
      .filter((item) => item.gap > 0)
      .reduce((sum, item) => sum + item.gap, 0);

    const totalShortage = chartData
      .filter((item) => item.gap < 0)
      .reduce((sum, item) => sum + Math.abs(item.gap), 0);

    const avgGap = chartData.reduce((sum, item) => sum + item.gap, 0) / chartData.length;

    return {
      totalSurplus,
      totalShortage,
      avgGap,
      status: avgGap > 0 ? 'surplus' : avgGap < 0 ? 'shortage' : 'balanced',
    };
  }, [chartData]);

  const significantGaps = useMemo(() => {
    if (!chartData.length) return [];

    return chartData
      .filter((item) => Math.abs(item.gap) > 100)
      .sort((a, b) => Math.abs(b.gap) - Math.abs(a.gap))
      .slice(0, 5);
  }, [chartData]);

  const formatValue = (value) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toFixed(0);
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;

    const gap = payload[0].payload.gap;
    const demand = payload[0].payload.demand;
    const supply = payload[0].payload.supply;

    return (
      <div
        style={{
          backgroundColor: 'var(--card-bg)',
          border: '1px solid var(--border-color)',
          borderRadius: '6px',
          padding: '12px',
        }}
      >
        <p style={{ margin: '0 0 8px 0', fontWeight: 600 }}>{label}</p>
        <p style={{ margin: '4px 0', fontSize: '14px' }}>Demand: {formatValue(demand)}</p>
        <p style={{ margin: '4px 0', fontSize: '14px' }}>Supply: {formatValue(supply)}</p>
        <p
          style={{
            margin: '4px 0',
            fontSize: '14px',
            fontWeight: 600,
            color: gap > 0 ? '#10b981' : gap < 0 ? '#ef4444' : '#6b7280',
          }}
        >
          Gap: {gap > 0 ? '+' : ''}
          {formatValue(gap)} ({gap > 0 ? 'Surplus' : gap < 0 ? 'Shortage' : 'Balanced'})
        </p>
      </div>
    );
  };

  if (!data?.gaps || data.gaps.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>Demand-Supply Gap Analysis</h2>
        </div>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>📊</div>
          <p>No gap analysis data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Demand-Supply Gap Analysis</h2>
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

      <div className={styles.chartSection}>
        <ChartContainer isLoading={isLoading} height={400}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
              <XAxis dataKey="date" />
              <YAxis tickFormatter={formatValue} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="var(--border-color)" strokeWidth={2} />
              <Bar dataKey="gap" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.gap > 0 ? '#10b981' : entry.gap < 0 ? '#ef4444' : '#6b7280'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {summary && (
        <div className={styles.summary}>
          <div className={styles.summaryCard}>
            <div className={styles.summaryLabel}>Total Surplus</div>
            <div className={`${styles.summaryValue} ${styles.surplus}`}>
              +{formatValue(summary.totalSurplus)}
            </div>
            <div className={styles.summarySubtext}>Excess inventory</div>
          </div>
          <div className={styles.summaryCard}>
            <div className={styles.summaryLabel}>Total Shortage</div>
            <div className={`${styles.summaryValue} ${styles.shortage}`}>
              -{formatValue(summary.totalShortage)}
            </div>
            <div className={styles.summarySubtext}>Unmet demand</div>
          </div>
          <div className={styles.summaryCard}>
            <div className={styles.summaryLabel}>Average Gap</div>
            <div className={`${styles.summaryValue} ${styles[summary.status]}`}>
              {summary.avgGap > 0 ? '+' : ''}
              {formatValue(summary.avgGap)}
            </div>
            <div className={styles.summarySubtext}>
              {summary.status === 'surplus'
                ? 'Oversupplied'
                : summary.status === 'shortage'
                ? 'Undersupplied'
                : 'Balanced'}
            </div>
          </div>
        </div>
      )}

      {significantGaps.length > 0 && (
        <div className={styles.gapList}>
          <h3 className={styles.gapListTitle}>Significant Gaps</h3>
          <div className={styles.gapItems}>
            {significantGaps.map((item, index) => (
              <div
                key={index}
                className={`${styles.gapItem} ${item.gap > 0 ? styles.surplus : styles.shortage}`}
              >
                <div className={styles.gapItemLeft}>
                  <div className={styles.gapItemDate}>{item.date}</div>
                  <div className={styles.gapItemDetails}>
                    Demand: {formatValue(item.demand)} | Supply: {formatValue(item.supply)}
                  </div>
                </div>
                <div className={styles.gapItemRight}>
                  <div className={`${styles.gapValue} ${item.gap > 0 ? styles.surplus : styles.shortage}`}>
                    {item.gap > 0 ? '+' : ''}
                    {formatValue(item.gap)}
                  </div>
                  <div className={styles.gapPercentage}>
                    {((Math.abs(item.gap) / item.demand) * 100).toFixed(1)}% gap
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
