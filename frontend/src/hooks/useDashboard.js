import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../services/dashboardService';
import { queryKeys } from '../lib/queryClient';

/**
 * Hook to fetch dashboard overview data
 */
export const useDashboardOverview = (filters = {}) => {
  return useQuery({
    queryKey: queryKeys.dashboard.overview(filters),
    queryFn: () => dashboardService.getOverview(filters),
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // Refetch every 5 minutes
    retry: 3,
    retryDelay: 1000,
  });
};

/**
 * Hook to fetch KPI metrics
 */
export const useKPIMetrics = (timeRange = '30d') => {
  return useQuery({
    queryKey: queryKeys.dashboard.kpis(timeRange),
    queryFn: () => dashboardService.getKPIMetrics(timeRange),
    staleTime: 60000, // 1 minute
    retry: 3, // Retry failed requests
    retryDelay: 1000, // Wait 1 second between retries
  });
};

/**
 * Hook to fetch trend data
 */
export const useTrendData = (metric, timeRange = '30d') => {
  return useQuery({
    queryKey: queryKeys.dashboard.trends(metric, timeRange),
    queryFn: () => dashboardService.getTrendData(metric, timeRange),
    enabled: !!metric,
    staleTime: 300000, // 5 minutes
    retry: 3,
    retryDelay: 1000,
  });
};

/**
 * Hook to fetch alerts
 */
export const useAlerts = (filters = {}) => {
  return useQuery({
    queryKey: queryKeys.dashboard.alerts(filters),
    queryFn: () => dashboardService.getAlerts(filters),
    staleTime: 60000, // 1 minute
    refetchInterval: 120000, // Refetch every 2 minutes
    retry: 3,
    retryDelay: 1000,
  });
};

/**
 * Hook to fetch quick insights
 */
export const useQuickInsights = (limit = 5) => {
  return useQuery({
    queryKey: queryKeys.dashboard.insights(limit),
    queryFn: () => dashboardService.getQuickInsights(limit),
    staleTime: 300000, // 5 minutes
    retry: 3,
    retryDelay: 1000,
  });
};

/**
 * Hook to fetch recent activity
 */
export const useRecentActivity = (limit = 10) => {
  return useQuery({
    queryKey: queryKeys.dashboard.activity(limit),
    queryFn: () => dashboardService.getRecentActivity(limit),
    staleTime: 60000, // 1 minute
  });
};
