import { create } from 'zustand';

/**
 * Notification store using Zustand
 * Manages toast notifications and alerts
 */
export const useNotificationStore = create((set, get) => ({
  // State
  notifications: [],
  unreadCount: 0,

  // Actions
  addNotification: (notification) => {
    const id = Date.now() + Math.random();
    const newNotification = {
      id,
      type: 'info', // info, success, warning, error
      title: '',
      message: '',
      duration: 5000, // Auto-dismiss after 5 seconds
      dismissible: true,
      timestamp: new Date().toISOString(),
      read: false,
      ...notification,
    };

    set((state) => ({
      notifications: [newNotification, ...state.notifications],
      unreadCount: state.unreadCount + 1,
    }));

    // Auto-dismiss if duration is set
    if (newNotification.duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, newNotification.duration);
    }

    return id;
  },

  removeNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  markAsRead: (id) => {
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    }));
  },

  markAllAsRead: () => {
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    }));
  },

  clearAll: () => {
    set({ notifications: [], unreadCount: 0 });
  },

  clearRead: () => {
    set((state) => ({
      notifications: state.notifications.filter((n) => !n.read),
    }));
  },

  // Convenience methods for different notification types
  success: (message, title = 'Success') => {
    return get().addNotification({
      type: 'success',
      title,
      message,
    });
  },

  error: (message, title = 'Error') => {
    return get().addNotification({
      type: 'error',
      title,
      message,
      duration: 0, // Don't auto-dismiss errors
    });
  },

  warning: (message, title = 'Warning') => {
    return get().addNotification({
      type: 'warning',
      title,
      message,
    });
  },

  info: (message, title = 'Info') => {
    return get().addNotification({
      type: 'info',
      title,
      message,
    });
  },

  // Getters
  getUnreadCount: () => get().unreadCount,
  getNotifications: () => get().notifications,
  getUnreadNotifications: () => get().notifications.filter((n) => !n.read),
}));
