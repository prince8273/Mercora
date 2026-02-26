// Export all custom hooks
// Note: useAuth is exported from contexts/AuthContext.jsx
export { 
  useQueryHistory, 
  useQueryById, 
  useExecuteQuery, 
  useQuerySuggestions,
  useCancelQuery,
  useExportResults 
} from './useQuery';
export { 
  useCompetitorPricing, 
  usePriceTrends, 
  usePricingRecommendations,
  usePromotionAnalysis,
  useApplyPricing,
  useSimulatePricing
} from './usePricing';
export { 
  useSentimentOverview, 
  useSentimentTrends, 
  useThemeBreakdown,
  useReviews,
  useFeatureRequests,
  useComplaintAnalysis
} from './useSentiment';
export { 
  useDemandForecast, 
  useInventoryRecommendations, 
  useForecastAccuracy,
  useDemandSupplyGap,
  useGenerateForecast,
  useAdjustForecast
} from './useForecast';
export { 
  useDashboardOverview, 
  useKPIMetrics, 
  useTrendData,
  useAlerts,
  useQuickInsights,
  useRecentActivity
} from './useDashboard';
export { 
  useWebSocket, 
  useQueryProgress, 
  useNotifications,
  useRealtimeAlerts,
  useDataUpdates
} from './useWebSocket';
export { useDebounce, useDebouncedCallback } from './useDebounce';
