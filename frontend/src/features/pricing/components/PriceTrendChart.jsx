import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { ChartContainer } from '../../../components/molecules/ChartContainer';
import { Button } from '../../../components/atoms/Button';
import styles from './PriceTrendChart.module.css';

const TIME_RANGES = [
  { value: '7d', label: '7 Days' },
  { value: '30d', label: '30 Days' },
  { value: '90d', label: '90 Days' },
  { value: 'custom', label: 'Custom' },
];

export const PriceTrendChart = ({
  data = [],
  yourPriceKey = 'yourPrice',
  competitorKeys = [],
  loading = false,
  error = null,
  onTimeRangeChange,
  className = '',
  ...props
}) => {
  const [timeRange, setTimeRange] = useState('30d');
  const [hiddenLines, setHiddenLines] = useState(new Set());

  const colors = {
    yourPrice: 'var(--primary-color)',
    competitor1: 'var(--error-color)',
    competitor2: 'var(--warning-color)',
    competitor3: 'var(--info-color)',
    competitor4: 'var(--success-color)',
  };

  const handleTimeRangeChange = (range) => {
    setTimeRange(range);
    if (onTimeRangeChange) {
      onTimeRangeChange(range);
    }
  };

  const handleLegendClick = (dataKey) => {
    setHiddenLines((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(dataKey)) {
        newSet.delete(dataKey);
      } else {
        newSet.add(dataKey);
      }
      return newSet;
    });
  };

  const formatPrice = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (value) => {
    const date = new Date(value);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || payload.length === 0) return null;

    return (
      <div className={styles.tooltip}>
        <p className={styles.tooltipLabel}>{formatDate(label)}</p>
        <div className={styles.tooltipContent}>
          {payload.map((entry, index) => (
            <div key={index} className={styles.tooltipItem}>
              <span
                className={styles.tooltipDot}
                style={{ backgroundColor: entry.color }}
              />
              <span className={styles.tooltipName}>{entry.name}:</span>
              <span className={styles.tooltipValue}>
                {formatPrice(entry.value)}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const CustomLegend = ({ payload }) => {
    return (
      <div className={styles.legend}>
        {payload.map((entry, index) => {
          const isHidden = hiddenLines.has(entry.dataKey);
          return (
            <button
              key={index}
              className={`${styles.legendItem} ${isHidden ? styles.legendItemHidden : ''}`}
              onClick={() => handleLegendClick(entry.dataKey)}
              type="button"
            >
              <span
                className={styles.legendDot}
                style={{
                  backgroundColor: isHidden ? 'var(--text-tertiary)' : entry.color,
                }}
              />
              <span className={styles.legendText}>{entry.value}</span>
            </button>
          );
        })}
      </div>
    );
  };

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <h3 className={styles.title}>Price Trends</h3>
        <div className={styles.timeRangeSelector}>
          {TIME_RANGES.map((range) => (
            <button
              key={range.value}
              className={`${styles.timeRangeButton} ${
                timeRange === range.value ? styles.active : ''
              }`}
              onClick={() => handleTimeRangeChange(range.value)}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      <ChartContainer
        loading={loading}
        error={error}
        height={400}
        showLegend={false}
      >
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="var(--text-tertiary)"
              style={{ fontSize: '0.75rem' }}
            />
            <YAxis
              tickFormatter={formatPrice}
              stroke="var(--text-tertiary)"
              style={{ fontSize: '0.75rem' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend content={<CustomLegend />} />

            {/* Your Price Line */}
            <Line
              type="monotone"
              dataKey={yourPriceKey}
              name="Your Price"
              stroke={colors.yourPrice}
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              hide={hiddenLines.has(yourPriceKey)}
            />

            {/* Competitor Lines */}
            {competitorKeys.map((key, index) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                name={key.replace('competitor', 'Competitor ')}
                stroke={colors[`competitor${index + 1}`] || 'var(--text-tertiary)'}
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
                hide={hiddenLines.has(key)}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </ChartContainer>
    </div>
  );
};
