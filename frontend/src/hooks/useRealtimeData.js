import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { wsManager } from '../lib/websocket';
import { queryKeys } from '../lib/queryClient';
import { useToast } from '../components/organisms/ToastManager';

/**
 * Hook for real-time data updates via WebSocket
 */
export const useRealtimeData = (options = {}) => {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { showNotifications = true, dataTypes = [] } = options;

  useEffect(() => {
    // Check if WebSocket is available
    if (wsManager.isPollingFallback()) {
      console.log('WebSocket unavailable. Real-time updates disabled.');
      return;
    }

    // Ensure WebSocket is connected
    if (!wsManager.isConnected()) {
      wsManager.connect();
    }

    // Subscribe to data update events
    const handleDataUpdate = (data) => {
      const { type, message } = data;

      // Filter by data types if specified
      if (dataTypes.length > 0 && !dataTypes.includes(type)) {
        return;
      }

      // Invalidate relevant queries based on data type
      switch (type) {
        case 'dashboard':
          queryClient.invalidateQueries(queryKeys.dashboard.overview());
          queryClient.invalidateQueries(queryKeys.dashboard.kpis());
          queryClient.invalidateQueries(queryKeys.dashboard.trends());
          break;

        case 'kpis':
          queryClient.invalidateQueries(queryKeys.dashboard.kpis());
          break;

        case 'alerts':
          queryClient.invalidateQueries(queryKeys.dashboard.alerts());
          break;

        case 'pricing':
          queryClient.invalidateQueries(queryKeys.pricing.competitor());
          queryClient.invalidateQueries(queryKeys.pricing.trends());
          queryClient.invalidateQueries(queryKeys.pricing.recommendations());
          break;

        case 'sentiment':
          queryClient.invalidateQueries(queryKeys.sentiment.overview());
          queryClient.invalidateQueries(queryKeys.sentiment.reviews());
          break;

        case 'forecast':
          queryClient.invalidateQueries(queryKeys.forecast.demand());
          queryClient.invalidateQueries(queryKeys.forecast.inventory());
          break;

        default:
          console.log('Unknown data update type:', type);
      }

      // Show notification if enabled
      if (showNotifications && message) {
        toast.info('Data Updated', message, 3000);
      }
    };

    // Subscribe to data:updated event
    const unsubscribe = wsManager.subscribe('data:updated', handleDataUpdate);

    // Cleanup on unmount
    return () => {
      unsubscribe();
    };
  }, [queryClient, toast, showNotifications, dataTypes]);
};

/**
 * Hook for dashboard real-time updates
 */
export const useDashboardRealtime = (showNotifications = false) => {
  return useRealtimeData({
    showNotifications,
    dataTypes: ['dashboard', 'kpis', 'alerts'],
  });
};

/**
 * Hook for pricing real-time updates
 */
export const usePricingRealtime = (showNotifications = false) => {
  return useRealtimeData({
    showNotifications,
    dataTypes: ['pricing'],
  });
};

/**
 * Hook for sentiment real-time updates
 */
export const useSentimentRealtime = (showNotifications = false) => {
  return useRealtimeData({
    showNotifications,
    dataTypes: ['sentiment'],
  });
};
