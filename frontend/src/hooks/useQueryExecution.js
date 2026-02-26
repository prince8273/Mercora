import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { wsManager } from '../lib/websocket';
import { queryKeys } from '../lib/queryClient';
import { debounce } from 'lodash';

/**
 * Hook for real-time query execution with WebSocket progress tracking
 */
export const useQueryExecution = (queryId) => {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle'); // idle, active, completed, error
  const [currentActivity, setCurrentActivity] = useState('');
  const [activityLog, setActivityLog] = useState([]);
  const [estimatedTime, setEstimatedTime] = useState(null);
  const [error, setError] = useState(null);
  const queryIdRef = useRef(null);
  const unsubscribersRef = useRef([]);

  // Debounced cache invalidation to prevent excessive updates
  const invalidateQueryCache = useCallback(
    debounce((qId) => {
      queryClient.invalidateQueries(queryKeys.queries.detail(qId));
      queryClient.invalidateQueries(queryKeys.queries.list());
    }, 500),
    [queryClient]
  );

  useEffect(() => {
    if (!queryId) return;

    queryIdRef.current = queryId;

    // Check if WebSocket is available
    const isConnected = wsManager.isConnected();
    const isPollingFallback = wsManager.isPollingFallback();

    if (!isConnected && !isPollingFallback) {
      // Try to connect
      wsManager.connect();
    }

    if (isPollingFallback) {
      console.log('WebSocket unavailable. Using polling mode for query progress.');
      // Implement polling fallback
      startPolling(queryId);
      return;
    }

    // Subscribe to query progress events
    const handleProgress = (data) => {
      if (data.queryId === queryId) {
        setProgress(data.progress || 0);
        setStatus('active');
        setCurrentActivity(data.activity || '');
        setEstimatedTime(data.estimatedTime || null);

        // Add to activity log
        if (data.activity) {
          setActivityLog((prev) => [
            ...prev,
            {
              timestamp: new Date(),
              message: data.activity,
            },
          ].slice(-10)); // Keep last 10 activities
        }
      }
    };

    const handleComplete = (data) => {
      if (data.queryId === queryId) {
        setProgress(100);
        setStatus('completed');
        setCurrentActivity('Query completed successfully');
        setEstimatedTime(0);

        // Invalidate cache to fetch fresh results
        invalidateQueryCache(queryId);
      }
    };

    const handleError = (data) => {
      if (data.queryId === queryId) {
        setStatus('error');
        setError(data.error || 'Query execution failed');
        setCurrentActivity('');
        setEstimatedTime(null);
      }
    };

    // Subscribe to events
    const unsubProgress = wsManager.subscribe('query:progress', handleProgress);
    const unsubComplete = wsManager.subscribe('query:complete', handleComplete);
    const unsubError = wsManager.subscribe('query:error', handleError);

    unsubscribersRef.current = [unsubProgress, unsubComplete, unsubError];

    // Cleanup on unmount or queryId change
    return () => {
      unsubscribersRef.current.forEach((unsub) => unsub());
      unsubscribersRef.current = [];
      queryIdRef.current = null;
    };
  }, [queryId, queryClient, invalidateQueryCache]);

  // Polling fallback when WebSocket is unavailable
  const startPolling = (qId) => {
    const pollInterval = setInterval(async () => {
      try {
        // Fetch query status from API
        const result = await queryClient.fetchQuery(
          queryKeys.queries.detail(qId)
        );

        if (result) {
          setProgress(result.progress || 0);
          setStatus(result.status || 'active');
          setCurrentActivity(result.currentActivity || '');
          setEstimatedTime(result.estimatedTime || null);

          if (result.status === 'completed') {
            clearInterval(pollInterval);
            setProgress(100);
            setStatus('completed');
          } else if (result.status === 'error') {
            clearInterval(pollInterval);
            setStatus('error');
            setError(result.error || 'Query execution failed');
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000); // Poll every 2 seconds

    // Cleanup
    return () => clearInterval(pollInterval);
  };

  const reset = useCallback(() => {
    setProgress(0);
    setStatus('idle');
    setCurrentActivity('');
    setActivityLog([]);
    setEstimatedTime(null);
    setError(null);
  }, []);

  return {
    progress,
    status,
    currentActivity,
    activityLog,
    estimatedTime,
    error,
    reset,
    isPollingMode: wsManager.isPollingFallback(),
  };
};
