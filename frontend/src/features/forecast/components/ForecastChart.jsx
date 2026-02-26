import { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { ChartContainer } from '../../../components/molecules/ChartContainer/ChartContainer';
import styles from './ForecastChart.module.css';

export default function ForecastChart({ data, isLoading, horizon, onHorizonChange }) {
  const chartData = useMemo(() => {
    if (!data?.historical || !data?.forecast) return [];

    const historical = data.historical.map((item) => ({
      ...item,
      type: 'historical',
    }));

    const forecast = data.forecast.map((item) => ({
      ...item,
      type: 'forecast',
    }));

    return [...historical, ...forecast];
  }, [data]);

  const separatorIndex = useMemo(() => {
    if (!data?.historical) return 0;
    return data.historical.length - 1;
  }, [data]);

  const stats = useMemo(() => {
    if (!data?.stats) return null;
    return data.stats;
  }, [data]);

  const formatValue = (value) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toFixed(0);
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;

    const isHistorical = payload[0]?.payload?.type === 'historical';

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
        {payload.map((entry, index) => {
          if (entry.dataKey === 'confidenceLower' || entry.dataKey === 'confidenceUpper')
            return null;

          return (
            <p
              key={index}
              style={{
                margin: '4px 0',
                color: entry.color,
                fontSize: '14px',
              }}
            >
              {isHistorical ? 'Actual' : 'Forecast'}: {formatValue(entry.value)}
            </p>
          );
        })}
        {!isHistorical && payload[0]?.payload?.confidenceLower && (
          <p style={{ margin: '4px 0', fontSize: '12px', color: 'var(--text-secondary)' }}>
            Range: {formatValue(payload[0].payload.confidenceLower)} -{' '}
            {formatValue(payload[0].payload.confidenceUpper)}
          </p>
        )}
      </div>
    );
  };

  if (!data || !chartData.length) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>Demand Forecast</h2>
        </div>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>📈</div>
          <p>No forecast data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Demand Forecast</h2>
        <div className={styles.controls}>
          <div className={styles.horizonSelector}>
            <button
              className={`${styles.horizonButton} ${horizon === '7d' ? styles.active : ''}`}
              onClick={() => onHorizonChange?.('7d')}
            >
              7 Days
            </button>
            <button
              className={`${styles.horizonButton} ${horizon === '30d' ? styles.active : ''}`}
              onClick={() => onHorizonChange?.('30d')}
            >
              30 Days
            </button>
            <button
              className={`${styles.horizonButton} ${horizon === '90d' ? styles.active : ''}`}
              onClick={() => onHorizonChange?.('90d')}
            >
              90 Days
            </button>
          </div>
        </div>
      </div>

      <div className={styles.chartSection}>
        <ChartContainer isLoading={isLoading} height={400}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
              <XAxis dataKey="date" />
              <YAxis tickFormatter={formatValue} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />

              {/* Confidence band */}
              <Area
                type="monotone"
                dataKey="confidenceUpper"
                stroke="none"
                fill="#10b981"
                fillOpacity={0.1}
                name="Confidence Band"
              />
              <Area
                type="monotone"
                dataKey="confidenceLower"
                stroke="none"
                fill="#10b981"
                fillOpacity={0.1}
              />

              {/* Historical data */}
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: '#3b82f6', r: 4 }}
                name="Historical"
                connectNulls={false}
              />

              {/* Forecast data */}
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="#10b981"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: '#10b981', r: 4 }}
                name="Forecast"
                connectNulls={false}
              />

              {/* Separator line */}
              {separatorIndex > 0 && (
                <ReferenceLine
                  x={chartData[separatorIndex]?.date}
                  stroke="var(--border-color)"
                  strokeWidth={2}
                  strokeDasharray="3 3"
                  label={{ value: 'Today', position: 'top' }}
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <div className={`${styles.legendColor} ${styles.historical}`} />
          <span>Historical Data (Actual)</span>
        </div>
        <div className={styles.legendItem}>
          <div className={`${styles.legendColor} ${styles.forecast}`} />
          <span>Forecast (Predicted)</span>
        </div>
        <div className={styles.legendItem}>
          <div className={`${styles.legendColor} ${styles.confidence}`} />
          <span>Confidence Band (95%)</span>
        </div>
      </div>

      {stats && (
        <div className={styles.stats}>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>Avg Historical Demand</div>
            <div className={styles.statValue}>{formatValue(stats.avgHistorical)}</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>Avg Forecast Demand</div>
            <div className={styles.statValue}>{formatValue(stats.avgForecast)}</div>
            <div
              className={`${styles.statChange} ${
                stats.change >= 0 ? styles.positive : styles.negative
              }`}
            >
              {stats.change >= 0 ? '↑' : '↓'} {Math.abs(stats.change).toFixed(1)}%
            </div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>Peak Demand</div>
            <div className={styles.statValue}>{formatValue(stats.peakDemand)}</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>Confidence Level</div>
            <div className={styles.statValue}>{stats.confidence}%</div>
          </div>
        </div>
      )}
    </div>
  );
}
