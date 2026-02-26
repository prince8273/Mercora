import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t, i18n } = useTranslation();
  
  // Read default date range from user preferences (localStorage)
  const getDefaultTimeRange = () => {
    try {
      const preferences = JSON.parse(localStorage.getItem('userPreferences') || '{}');
      console.log('🔧 Loading preferences:', preferences);
      console.log('🔧 Default date range:', preferences.defaultDateRange);
      return preferences.defaultDateRange || '30d';
    } catch (error) {
      console.error('🔧 Error loading preferences:', error);
      return '30d';
    }
  };

  const [timeRange, setTimeRange] = useState(getDefaultTimeRange());
  const [showReloadPrompt, setShowReloadPrompt] = useState(false);
  const [pendingTimeRange, setPendingTimeRange] = useState(null);

  // Debug: Log the current timeRange
  React.useEffect(() => {
    console.log('⏰ Current timeRange:', timeRange);
    console.log('⏰ Preferences:', localStorage.getItem('userPreferences'));
  }, [timeRange]);

  // Listen for localStorage changes from other tabs
  React.useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'userPreferences' && e.newValue) {
        try {
          const preferences = JSON.parse(e.newValue);
          if (preferences.defaultDateRange && preferences.defaultDateRange !== timeRange) {
            // Don't auto-update, show prompt instead
            setPendingTimeRange(preferences.defaultDateRange);
            setShowReloadPrompt(true);
          }
        } catch (error) {
          console.error('Failed to parse preferences from storage event:', error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [timeRange]);

  const handleReloadData = () => {
    if (pendingTimeRange) {
      setTimeRange(pendingTimeRange);
      setShowReloadPrompt(false);
      setPendingTimeRange(null);
    }
  };

  const handleDismissPrompt = () => {
    setShowReloadPrompt(false);
    setPendingTimeRange(null);
  };

  // Format time range for display
  const formatTimeRangePeriod = (range) => {
    const rangeMap = {
      '7d': 'last 7 days',
      '30d': 'last 30 days',
      '60d': 'last 60 days',
      '90d': 'last 90 days',
      '1y': 'last year',
      '365d': 'last year'
    };
    return rangeMap[range] || 'last period';
  };

  const periodLabel = formatTimeRangePeriod(timeRange);

  // Enable real-time updates for dashboard
  useDashboardRealtime(false); // Set to true to show notifications on updates

  // Fetch data using hooks
  const { data: overview, isLoading: overviewLoading, error: overviewError, refetch: refetchOverview } = useDashboardOverview();
  const { data: kpiData, isLoading: kpiLoading, error: kpiError } = useKPIMetrics(timeRange);
  const { data: trendData, isLoading: trendLoading, error: trendError } = useTrendData('revenue', timeRange);
  const { data: alerts, isLoading: alertsLoading, error: alertsError, refetch: refetchAlerts } = useAlerts();
  const { data: insights, isLoading: insightsLoading, error: insightsError } = useQuickInsights(5);

  // Debug logging
  React.useEffect(() => {
    if (trendData) {
      console.log('📊 Trend Data Keys:', Object.keys(trendData));
      console.log('📊 Trends Array:', trendData?.trends);
      console.log('📊 Trends Length:', trendData?.trends?.length);
      if (trendData?.trends?.length > 0) {
        console.log('📊 First 3 items:', trendData.trends.slice(0, 3));
      }
    }
    console.log('📊 Trend Loading:', trendLoading);
    console.log('📊 Trend Error:', trendError);
  }, [trendData, trendLoading, trendError]);

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
        title={t('dashboard.title')}
        breadcrumbs={[{ label: t('dashboard.title'), path: '/overview' }]}
        actions={
          <Button onClick={handleRefresh} variant="secondary" size="sm">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {t('dashboard.refresh')}
          </Button>
        }
      />

      {/* Reload Prompt Modal */}
      {showReloadPrompt && (
        <>
          {/* Backdrop */}
          <div 
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              zIndex: 9998,
              animation: 'fadeIn 0.2s ease-in-out'
            }}
            onClick={handleDismissPrompt}
          />
          
          {/* Modal */}
          <div style={{
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            zIndex: 9999,
            minWidth: '400px',
            maxWidth: '500px',
            animation: 'slideIn 0.3s ease-out'
          }}>
            {/* Icon */}
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              backgroundColor: '#fef3c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '16px'
            }}>
              <svg width="24" height="24" fill="#f59e0b" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>

            {/* Title */}
            <h3 style={{
              fontSize: '18px',
              fontWeight: '600',
              color: '#111827',
              marginBottom: '8px'
            }}>
              Settings Updated
            </h3>

            {/* Message */}
            <p style={{
              fontSize: '14px',
              color: '#6b7280',
              marginBottom: '24px',
              lineHeight: '1.5'
            }}>
              The date range settings have been changed in another tab. Would you like to reload the dashboard with the new settings?
            </p>

            {/* Actions */}
            <div style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'flex-end'
            }}>
              <Button onClick={handleDismissPrompt} variant="secondary" size="md">
                Keep Current Data
              </Button>
              <Button onClick={handleReloadData} variant="primary" size="md">
                Reload Dashboard
              </Button>
            </div>
          </div>

          {/* Add animations */}
          <style>{`
            @keyframes fadeIn {
              from { opacity: 0; }
              to { opacity: 1; }
            }
            @keyframes slideIn {
              from {
                opacity: 0;
                transform: translate(-50%, -48%);
              }
              to {
                opacity: 1;
                transform: translate(-50%, -50%);
              }
            }
          `}</style>
        </>
      )}

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
              title={t('dashboard.totalRevenue')}
              value={kpiData?.gmv?.value || 0}
              change={kpiData?.gmv?.change || 0}
              trend={kpiData?.gmv?.trend || (kpiData?.gmv?.change >= 0 ? 'up' : 'down')}
              format="currency"
              period={periodLabel}
            />
            <MetricCard
              title={t('dashboard.profitMargin')}
              value={kpiData?.margin?.value || 0}
              change={kpiData?.margin?.change || 0}
              trend={kpiData?.margin?.trend || (kpiData?.margin?.change >= 0 ? 'up' : 'down')}
              format="percentage"
              period={periodLabel}
            />
            <MetricCard
              title={t('dashboard.conversionRate')}
              value={kpiData?.conversion?.value || 0}
              change={kpiData?.conversion?.change || 0}
              trend={kpiData?.conversion?.trend || (kpiData?.conversion?.change >= 0 ? 'up' : 'down')}
              format="percentage"
              period={periodLabel}
            />
            <MetricCard
              title={t('dashboard.inventoryHealth')}
              value={kpiData?.inventory_health?.value || 0}
              change={kpiData?.inventory_health?.change || 0}
              trend={kpiData?.inventory_health?.trend || (kpiData?.inventory_health?.change >= 0 ? 'up' : 'down')}
              format="percentage"
              period={periodLabel}
            />
          </>
        )}
      </div>

      {/* Main Content Grid */}
      <div className="content-grid">
        {/* Trend Chart */}
        <div className="chart-section">
          <TrendChart
            data={trendData?.trends || []}
            xKey="date"
            yKeys={['revenue', 'orders']}
            title={t('dashboard.revenueOrdersTrend')}
            type="area"
            loading={trendLoading}
            error={trendError ? 'Failed to load trend data' : (trendData?.trends?.length === 0 ? 'No trend data available for this period' : null)}
            formatValue={(value) => value.toLocaleString()}
            formatXAxis={formatDate}
            height={350}
          />
        </div>

        {/* Alerts Panel */}
        <div className="alerts-section">
          <AlertPanel
            alerts={alerts?.alerts || []}
            loading={alertsLoading}
            onDismiss={handleDismissAlert}
          />
        </div>

        {/* Quick Insights */}
        <div className="insights-section">
          <QuickInsights
            insights={insights?.insights || []}
            loading={insightsLoading}
          />
        </div>
      </div>
    </div>
  );
}
