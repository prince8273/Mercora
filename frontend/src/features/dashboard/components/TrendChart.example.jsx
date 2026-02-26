import React from 'react';
import { TrendChart } from './TrendChart';

// Example data for demonstration
const sampleData = [
  { date: '2024-01', revenue: 45000, orders: 320, conversion: 3.2 },
  { date: '2024-02', revenue: 52000, orders: 380, conversion: 3.5 },
  { date: '2024-03', revenue: 48000, orders: 340, conversion: 3.1 },
  { date: '2024-04', revenue: 61000, orders: 420, conversion: 3.8 },
  { date: '2024-05', revenue: 58000, orders: 390, conversion: 3.6 },
  { date: '2024-06', revenue: 67000, orders: 450, conversion: 4.0 },
  { date: '2024-07', revenue: 72000, orders: 480, conversion: 4.2 },
];

export const TrendChartExamples = () => {
  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(value);
  };

  // Format percentage
  const formatPercentage = (value) => `${value}%`;

  // Format date
  const formatDate = (value) => {
    const date = new Date(value);
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  };

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <h1>TrendChart Examples</h1>

      {/* Example 1: Line Chart with Revenue */}
      <div>
        <h2>Revenue Trend (Line Chart)</h2>
        <TrendChart
          data={sampleData}
          xKey="date"
          yKeys={['revenue']}
          title="Monthly Revenue"
          type="line"
          formatValue={formatCurrency}
          formatXAxis={formatDate}
          height={350}
        />
      </div>

      {/* Example 2: Area Chart with Multiple Metrics */}
      <div>
        <h2>Multiple Metrics (Area Chart)</h2>
        <TrendChart
          data={sampleData}
          xKey="date"
          yKeys={['revenue', 'orders']}
          title="Revenue & Orders Trend"
          type="area"
          formatValue={(value) => value.toLocaleString()}
          formatXAxis={formatDate}
          height={350}
        />
      </div>

      {/* Example 3: Line Chart with Conversion Rate */}
      <div>
        <h2>Conversion Rate Trend</h2>
        <TrendChart
          data={sampleData}
          xKey="date"
          yKeys={['conversion']}
          title="Conversion Rate Over Time"
          type="line"
          formatValue={formatPercentage}
          formatXAxis={formatDate}
          height={300}
        />
      </div>

      {/* Example 4: Loading State */}
      <div>
        <h2>Loading State</h2>
        <TrendChart
          data={[]}
          xKey="date"
          yKeys={['revenue']}
          title="Loading Chart"
          loading={true}
          height={300}
        />
      </div>

      {/* Example 5: Error State */}
      <div>
        <h2>Error State</h2>
        <TrendChart
          data={[]}
          xKey="date"
          yKeys={['revenue']}
          title="Error Chart"
          error="Failed to load chart data. Please try again."
          height={300}
        />
      </div>

      {/* Example 6: Multiple Lines with Legend Toggle */}
      <div>
        <h2>All Metrics (Toggle Legend)</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1rem' }}>
          Click on legend items to show/hide lines
        </p>
        <TrendChart
          data={sampleData}
          xKey="date"
          yKeys={['revenue', 'orders', 'conversion']}
          title="All Metrics Comparison"
          type="line"
          formatValue={(value) => value.toLocaleString()}
          formatXAxis={formatDate}
          height={400}
          showLegend={true}
        />
      </div>
    </div>
  );
};
