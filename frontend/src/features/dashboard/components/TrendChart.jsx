import React, { useState } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { ChartContainer } from '../../../components/molecules/ChartContainer';
import styles from './TrendChart.module.css';

export const TrendChart = ({
  data = [],
  xKey = 'date',
  yKeys = [],
  title,
  type = 'line', // 'line' or 'area'
  loading = false,
  error,
  height = 400,
  showLegend = true,
  formatValue = (value) => value,
  formatXAxis = (value) => value,
  className = '',
  ...props
}) => {
  const [hiddenLines, setHiddenLines] = useState(new Set());

  // Chart colors for different lines
  const colors = [
    'var(--primary-color)',
    'var(--success-color)',
    'var(--warning-color)',
    'var(--info-color)',
    'var(--error-color)',
  ];

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

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || payload.length === 0) return null;

    return (
      <div className={styles.tooltip}>
        <p className={styles.tooltipLabel}>{formatXAxis(label)}</p>
        <div className={styles.tooltipContent}>
          {payload.map((entry, index) => (
            <div key={index} className={styles.tooltipItem}>
              <span
                className={styles.tooltipDot}
                style={{ backgroundColor: entry.color }}
              />
              <span className={styles.tooltipName}>{entry.name}:</span>
              <span className={styles.tooltipValue}>
                {formatValue(entry.value)}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const CustomLegend = ({ payload }) => {
    if (!showLegend) return null;

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
                style={{ backgroundColor: isHidden ? 'var(--text-tertiary)' : entry.color }}
              />
              <span className={styles.legendText}>{entry.value}</span>
            </button>
          );
        })}
      </div>
    );
  };

  const renderChart = () => {
    const ChartComponent = type === 'area' ? AreaChart : LineChart;
    const DataComponent = type === 'area' ? Area : Line;

    return (
      <ResponsiveContainer width="100%" height={height}>
        <ChartComponent data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis
            dataKey={xKey}
            tickFormatter={formatXAxis}
            stroke="var(--text-tertiary)"
            style={{ fontSize: '0.75rem' }}
          />
          <YAxis
            tickFormatter={formatValue}
            stroke="var(--text-tertiary)"
            style={{ fontSize: '0.75rem' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend content={<CustomLegend />} />
          {yKeys.map((key, index) => {
            const color = colors[index % colors.length];
            const isHidden = hiddenLines.has(key);

            if (type === 'area') {
              return (
                <Area
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={color}
                  fill={color}
                  fillOpacity={0.2}
                  strokeWidth={2}
                  hide={isHidden}
                  dot={false}
                  activeDot={{ r: 6 }}
                />
              );
            }

            return (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={color}
                strokeWidth={2}
                hide={isHidden}
                dot={false}
                activeDot={{ r: 6 }}
              />
            );
          })}
        </ChartComponent>
      </ResponsiveContainer>
    );
  };

  return (
    <ChartContainer
      title={title}
      loading={loading}
      error={error}
      height={height}
      showLegend={false}
      className={`${styles.container} ${className}`}
      {...props}
    >
      {renderChart()}
    </ChartContainer>
  );
};
