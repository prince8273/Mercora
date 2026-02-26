import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../../test/utils';
import { TrendChart } from './TrendChart';

// Mock Recharts components
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div data-testid="responsive-container">{children}</div>,
  LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
  AreaChart: ({ children }) => <div data-testid="area-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  Area: () => <div data-testid="area" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
}));

describe('TrendChart', () => {
  const mockData = [
    { date: '2024-01-01', revenue: 1000, orders: 50 },
    { date: '2024-01-02', revenue: 1200, orders: 60 },
    { date: '2024-01-03', revenue: 1100, orders: 55 },
  ];

  it('renders chart with data', () => {
    render(
      <TrendChart
        data={mockData}
        xKey="date"
        yKeys={['revenue', 'orders']}
        title="Revenue Trend"
      />
    );

    expect(screen.getByText('Revenue Trend')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('renders line chart by default', () => {
    render(
      <TrendChart
        data={mockData}
        xKey="date"
        yKeys={['revenue']}
      />
    );

    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('renders area chart when type is area', () => {
    render(
      <TrendChart
        data={mockData}
        xKey="date"
        yKeys={['revenue']}
        type="area"
      />
    );

    expect(screen.getByTestId('area-chart')).toBeInTheDocument();
  });

  it('shows loading skeleton when loading prop is true', () => {
    const { container } = render(
      <TrendChart
        data={[]}
        xKey="date"
        yKeys={['revenue']}
        loading={true}
      />
    );

    // Check for skeleton elements
    const skeletons = container.querySelectorAll('[class*="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('shows error message when error prop is provided', () => {
    render(
      <TrendChart
        data={[]}
        xKey="date"
        yKeys={['revenue']}
        error="Failed to load data"
      />
    );

    expect(screen.getByText('Failed to load data')).toBeInTheDocument();
  });

  it('shows empty state when no data', () => {
    render(
      <TrendChart
        data={[]}
        xKey="date"
        yKeys={['revenue']}
      />
    );

    // ChartContainer should handle empty state
    const container = screen.getByTestId('responsive-container');
    expect(container).toBeInTheDocument();
  });
});
