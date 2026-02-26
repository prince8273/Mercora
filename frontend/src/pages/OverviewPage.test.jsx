import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test/utils';
import OverviewPage from './OverviewPage';
import * as dashboardHooks from '../hooks/useDashboard';

// Mock the dashboard hooks
vi.mock('../hooks/useDashboard', () => ({
  useDashboardOverview: vi.fn(),
  useKPIMetrics: vi.fn(),
  useTrendData: vi.fn(),
  useAlerts: vi.fn(),
  useQuickInsights: vi.fn(),
}));

// Mock the realtime hook
vi.mock('../hooks/useRealtimeData', () => ({
  useDashboardRealtime: vi.fn(),
}));

describe('OverviewPage', () => {
  const mockKPIData = {
    revenue: { value: 125000, change: 5.2 },
    margin: { value: 35, change: 2.1 },
    conversion: { value: 3.5, change: -0.5 },
    inventory: { value: 250000, change: 1.8 },
  };

  const mockTrendData = {
    data: [
      { date: '2024-01-01', revenue: 1000, orders: 50 },
      { date: '2024-01-02', revenue: 1200, orders: 60 },
    ],
  };

  const mockAlerts = {
    data: [
      {
        id: '1',
        type: 'critical',
        title: 'Low Stock',
        message: 'Product XYZ is low',
      },
    ],
  };

  const mockInsights = {
    data: [
      {
        id: '1',
        type: 'trend',
        title: 'Sales Up',
        summary: 'Sales increased 15%',
      },
    ],
  };

  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();

    // Setup default mock implementations
    dashboardHooks.useDashboardOverview.mockReturnValue({
      data: {},
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    dashboardHooks.useKPIMetrics.mockReturnValue({
      data: mockKPIData,
      isLoading: false,
      error: null,
    });

    dashboardHooks.useTrendData.mockReturnValue({
      data: mockTrendData,
      isLoading: false,
      error: null,
    });

    dashboardHooks.useAlerts.mockReturnValue({
      data: mockAlerts,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    dashboardHooks.useQuickInsights.mockReturnValue({
      data: mockInsights,
      isLoading: false,
      error: null,
    });
  });

  it('renders page header', () => {
    render(<OverviewPage />);

    expect(screen.getByText('Overview Dashboard')).toBeInTheDocument();
  });

  it('renders all 4 KPI metric cards', () => {
    render(<OverviewPage />);

    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    expect(screen.getByText('Gross Margin')).toBeInTheDocument();
    expect(screen.getByText('Conversion Rate')).toBeInTheDocument();
    expect(screen.getByText('Inventory Value')).toBeInTheDocument();
  });

  it('displays KPI values correctly', () => {
    render(<OverviewPage />);

    // Values are formatted by MetricCard component
    expect(screen.getByText(/125,000/)).toBeInTheDocument(); // Currency formatted
    expect(screen.getByText(/35/)).toBeInTheDocument(); // Percentage
    expect(screen.getByText(/3\.5/)).toBeInTheDocument(); // Percentage
    expect(screen.getByText(/250,000/)).toBeInTheDocument(); // Currency formatted
  });

  it('shows loading skeletons when data is loading', () => {
    dashboardHooks.useKPIMetrics.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    const { container } = render(<OverviewPage />);

    // Check for skeleton elements
    const skeletons = container.querySelectorAll('[class*="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('shows error state when KPI data fails to load', () => {
    dashboardHooks.useKPIMetrics.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Failed to load'),
    });

    render(<OverviewPage />);

    expect(screen.getByText('Failed to load KPI metrics')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('renders trend chart section', () => {
    render(<OverviewPage />);

    expect(screen.getByText('Revenue & Orders Trend')).toBeInTheDocument();
  });

  it('renders alert panel', () => {
    render(<OverviewPage />);

    expect(screen.getByText('Low Stock')).toBeInTheDocument();
  });

  it('renders quick insights', () => {
    render(<OverviewPage />);

    expect(screen.getByText('Sales Up')).toBeInTheDocument();
  });

  it('calls refetch when refresh button is clicked', async () => {
    const refetchOverview = vi.fn();
    const refetchAlerts = vi.fn();

    dashboardHooks.useDashboardOverview.mockReturnValue({
      data: {},
      isLoading: false,
      error: null,
      refetch: refetchOverview,
    });

    dashboardHooks.useAlerts.mockReturnValue({
      data: mockAlerts,
      isLoading: false,
      error: null,
      refetch: refetchAlerts,
    });

    render(<OverviewPage />);

    const refreshButton = screen.getByText('Refresh');
    refreshButton.click();

    await waitFor(() => {
      expect(refetchOverview).toHaveBeenCalled();
      expect(refetchAlerts).toHaveBeenCalled();
    });
  });

  it('renders without console errors', () => {
    const consoleSpy = vi.spyOn(console, 'error');

    render(<OverviewPage />);

    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });
});
