import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * UI state store using Zustand
 * Manages global UI state like sidebar, modals, theme, etc.
 */
export const useUIStore = create(
  persist(
    (set, get) => ({
      // Sidebar state
      sidebarCollapsed: false,
      sidebarWidth: 240,

      // Modal state
      activeModal: null,
      modalData: null,

      // Command palette
      commandPaletteOpen: false,

      // Notification center
      notificationCenterOpen: false,

      // Loading states
      globalLoading: false,
      loadingMessage: '',

      // Selected items
      selectedProduct: null,
      selectedTimeRange: '30d',

      // Filters
      activeFilters: {},

      // Actions - Sidebar
      toggleSidebar: () => set((state) => ({ 
        sidebarCollapsed: !state.sidebarCollapsed 
      })),
      
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      
      setSidebarWidth: (width) => set({ sidebarWidth: width }),

      // Actions - Modal
      openModal: (modalName, data = null) => set({ 
        activeModal: modalName, 
        modalData: data 
      }),
      
      closeModal: () => set({ 
        activeModal: null, 
        modalData: null 
      }),

      // Actions - Command Palette
      toggleCommandPalette: () => set((state) => ({ 
        commandPaletteOpen: !state.commandPaletteOpen 
      })),
      
      setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),

      // Actions - Notification Center
      toggleNotificationCenter: () => set((state) => ({ 
        notificationCenterOpen: !state.notificationCenterOpen 
      })),
      
      setNotificationCenterOpen: (open) => set({ notificationCenterOpen: open }),

      // Actions - Loading
      setGlobalLoading: (loading, message = '') => set({ 
        globalLoading: loading, 
        loadingMessage: message 
      }),

      // Actions - Selection
      setSelectedProduct: (product) => set({ selectedProduct: product }),
      
      setSelectedTimeRange: (timeRange) => set({ selectedTimeRange: timeRange }),

      // Actions - Filters
      setFilter: (key, value) => set((state) => ({
        activeFilters: { ...state.activeFilters, [key]: value }
      })),
      
      clearFilter: (key) => set((state) => {
        const { [key]: _, ...rest } = state.activeFilters;
        return { activeFilters: rest };
      }),
      
      clearAllFilters: () => set({ activeFilters: {} }),

      // Getters
      getActiveFilters: () => get().activeFilters,
      getSelectedProduct: () => get().selectedProduct,
      getSelectedTimeRange: () => get().selectedTimeRange,
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        sidebarWidth: state.sidebarWidth,
        selectedTimeRange: state.selectedTimeRange,
      }),
    }
  )
);
