import { useMutation, useQuery } from '@tanstack/react-query';
import { pricingService } from '../services/pricingService';
import { queryKeys } from '../lib/queryClient';

/**
 * Hook to fetch competitor pricing data
 */
export const useCompetitorPricing = (productId, filters = {}) => {
  return useQuery({
    queryKey: queryKeys.pricing.competitors(productId, filters),
    queryFn: () => pricingService.getCompetitorPricing(productId, filters),
    enabled: !!productId,
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook to fetch price trends
 */
export const usePriceTrends = (productId, timeRange = '30d') => {
  return useQuery({
    queryKey: queryKeys.pricing.trends(productId, timeRange),
    queryFn: () => pricingService.getPriceTrends(productId, timeRange),
    enabled: !!productId,
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook to fetch pricing recommendations
 */
export const usePricingRecommendations = (productId) => {
  return useQuery({
    queryKey: queryKeys.pricing.recommendations(productId),
    queryFn: () => pricingService.getPricingRecommendations(productId),
    enabled: !!productId,
    staleTime: 600000, // 10 minutes
  });
};

/**
 * Hook to fetch promotion analysis
 */
export const usePromotionAnalysis = (filters = {}) => {
  return useQuery({
    queryKey: queryKeys.pricing.promotions(filters),
    queryFn: () => pricingService.getPromotionAnalysis(filters),
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook to apply pricing recommendation
 */
export const useApplyPricing = () => {
  return useMutation({
    mutationFn: (pricingData) => pricingService.applyPricing(pricingData),
  });
};

/**
 * Hook to simulate pricing impact
 */
export const useSimulatePricing = () => {
  return useMutation({
    mutationFn: (simulationData) => pricingService.simulatePricing(simulationData),
  });
};
