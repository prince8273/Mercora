import React from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { pricingService } from '../services/pricingService';
import { queryKeys } from '../lib/queryClient';

/**
 * Hook to fetch competitor pricing data
 */
export const useCompetitorPricing = (productId, filters = {}) => {
  return useQuery({
    queryKey: queryKeys.pricing.competitors(productId, filters),
    queryFn: () => pricingService.getCompetitorMatrix(productId),
    enabled: !!productId && productId !== 'undefined' && productId.length === 36, // Valid UUID check
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook to fetch price trends
 */
export const usePriceTrends = (productId, timeRange = '30d') => {
  const isValidUUID = productId && typeof productId === 'string' && productId.length === 36;
  
  React.useEffect(() => {
    if (productId) {
      console.log('usePriceTrends called with productId:', productId, 'isValid:', isValidUUID);
    }
  }, [productId, isValidUUID]);

  return useQuery({
    queryKey: queryKeys.pricing.trends(productId, timeRange),
    queryFn: () => pricingService.getPriceTrends(productId, timeRange),
    enabled: isValidUUID,
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
    enabled: !!productId && productId !== 'undefined' && productId.length === 36, // Valid UUID check
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
