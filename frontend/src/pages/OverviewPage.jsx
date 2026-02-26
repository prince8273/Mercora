import React, { useState } from 'react';
import { MetricCard } from '../components/molecules/MetricCard';
import { TrendChart, AlertPanel, QuickInsights } from '../features/dashboard/components';
import { PageHeader } from '../components/molecules/PageHeader';
import { LoadingSkeleton } from '../components/molecules/LoadingSkeleton';
import { Button } from '../components/atoms/Button';
import {
  useDashboardOverview,
  useKPIMetrics,
  useTrendData,
  useAlerts,
  useQuickInsights,
} from '../hooks/useDashboard';
import { useDashboardRealtime } from '../hooks/useRealtimeData';
import './OverviewPage.css';

export default function OverviewPage() {
  const [timeRange, setTimeRange] = useState('30d');

  // Enable real-time updates for dashboard
  useDashboardRealtime(false); // Set to true to show notifications on updates

  // Fetch data using hooks
  const { data: overview, isLoading: overviewLoading, error: overviewError, refetch: refetchOverview } = useDashboardOverview();
  const { data: kpiData, isLoading: kpiLoading, error: kpiError } = useKPIMetrics(timeRange);
  const { data: trendData, isLoading: trendLoading, error: trendError } = useTrendData('revenue', timeRange);
  const { data: alerts, isLoading: alertsLoading, error: alertsError, refetch: refetchAlerts } = useAlerts();
  const { data: insights, isLoading: insightsLoading, error: insightsError } = useQuickInsights(5);

  const handleDismissAlert = (alertId) => {
    // In a real app, this would call an API to dismiss the alert
    console.log('Dismiss alert:', alertId);
    refetchAlerts();
  };

  const handleRefresh = () => {
    refetchOverview();
    refetchAlerts();
  };

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

  // Format date for chart
  const formatDate = (value) => {
    const date = new Date(value);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="page">
      <PageHeader
        title="Overview Dashboard"
        breadcrumbs={[{ label: 'Dashboard', path: '/overview' }]}
        actions={
          <Button onClick={handleRefresh} variant="secondary" size="sm">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </Button>
        }
      />

      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        {kpiLoading ? (
          <>
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
            <LoadingSkeleton variant="card" />
          </>
        ) : kpiError ? (
          <div className="error-state">
            <p>Failed to load KPI metrics</p>
            <Button onClick={() => window.location.reload()} size="sm">
              Retry
            </Button>
          </div>
        ) : (
          <>
            <MetricCard
              title="Total Revenue"
              value={kpiData?.gmv?.value || 0}
              change={kpiData?.gmv?.change || 0}
              trend={kpiData?.gmv?.trend || (kpiData?.gmv?.change >= 0 ? 'up' : 'down')}
              format="currency"
            />
            <MetricCard
              title="Profit Margin"
              value={kpiData?.margin?.value || 0}
              change={kpiData?.margin?.change || 0}
              trend={kpiData?.margin?.trend || (kpiData?.margin?.change >= 0 ? 'up' : 'down')}
              format="percentage"
            />
            <MetricCard
              title="Conversion Rate"
              value={kpiData?.conversion?.value || 0}
              change={kpiData?.conversion?.change || 0}
              trend={kpiData?.conversion?.trend || (kpiData?.conversion?.change >= 0 ? 'up' : 'down')}
              format="percentage"
            />
            <MetricCard
              title="Inventory Health"
              value={kpiData?.inventory_health?.value || 0}
              change={kpiData?.inventory_health?.change || 0}
              trend={kpiData?.inventory_health?.trend || (kpiData?.inventory_health?.change >= 0 ? 'up' : 'down')}
              format="percentage"
            />
          </>
        )}
      </div>

      {/* Main Content Grid */}
      <div className="content-grid">
        {/* Trend Chart */}
        <div className="chart-section">
          <TrendChart
            data={trendData?.payload?.trends || []}
            xKey="date"
            yKeys={['revenue', 'orders']}
            title="Revenue & Orders Trend"
            type="area"
            loading={trendLoading}
            error={trendError ? 'Failed to load trend data' : null}
            formatValue={(value) => value.toLocaleString()}
            formatXAxis={formatDate}
            height={350}
          />
        </div>

        {/* Alerts Panel */}
        <div className="alerts-section">
          <AlertPanel
            alerts={alerts?.payload?.alerts || []}
            loading={alertsLoading}
            onDismiss={handleDismissAlert}
          />
        </div>

        {/* Quick Insights */}
        <div className="insights-section">
          <QuickInsights
            insights={insights?.payload?.insights || []}
            loading={insightsLoading}
          />
        </div>
      </div>
    </div>
  );
}
