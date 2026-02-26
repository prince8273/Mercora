import { useEffect, useRef, useState } from 'react';
import { wsManager } from '../lib/websocket';

/**
 * Hook to manage WebSocket connection and subscriptions
 * @param {string} event - Event name to subscribe to
 * @param {function} callback - Callback function to handle event data
 * @param {object} options - Options for connection
 */
export const useWebSocket = (event, callback, options = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const callbackRef = useRef(callback);

  // Update callback ref when it changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    // Connect to WebSocket
    wsManager.connect();

    // Subscribe to connection status
    const handleConnect = () => setIsConnected(true);
    const handleDisconnect = () => setIsConnected(false);

    wsManager.on('connect', handleConnect);
    wsManager.on('disconnect', handleDisconnect);

    // Subscribe to the specific event
    if (event) {
      wsManager.on(event, (data) => {
        callbackRef.current(data);
      });
    }

    // Cleanup
    return () => {
      wsManager.off('connect', handleConnect);
      wsManager.off('disconnect', handleDisconnect);
      if (event) {
        wsManager.off(event, callbackRef.current);
      }
      
      // Disconnect if specified in options
      if (options.disconnectOnUnmount) {
        wsManager.disconnect();
      }
    };
  }, [event, options.disconnectOnUnmount]);

  return {
    isConnected,
    emit: wsManager.emit.bind(wsManager),
    disconnect: wsManager.disconnect.bind(wsManager),
  };
};

/**
 * Hook to subscribe to query execution progress
 */
export const useQueryProgress = (queryId, onProgress) => {
  return useWebSocket(
    queryId ? `query:${queryId}:progress` : null,
    onProgress
  );
};

/**
 * Hook to subscribe to real-time notifications
 */
export const useNotifications = (onNotification) => {
  return useWebSocket('notification', onNotification);
};

/**
 * Hook to subscribe to real-time alerts
 */
export const useRealtimeAlerts = (onAlert) => {
  return useWebSocket('alert', onAlert);
};

/**
 * Hook to subscribe to data updates
 */
export const useDataUpdates = (dataType, onUpdate) => {
  return useWebSocket(`data:${dataType}:update`, onUpdate);
};
