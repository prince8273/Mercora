import { useMutation, useQuery } from '@tanstack/react-query';
import { forecastService } from '../services/forecastService';
import { queryKeys } from '../lib/queryClient';

/**
 * Hook to fetch demand forecast
 */
export const useDemandForecast = (productId, horizon = '30d') => {
  return useQuery({
    queryKey: queryKeys.forecast.demand(productId, horizon),
    queryFn: () => forecastService.getDemandForecast(productId, horizon),
    enabled: !!productId,
    staleTime: 600000, // 10 minutes
  });
};

/**
 * Hook to fetch inventory recommendations
 */
export const useInventoryRecommendations = (productId) => {
  return useQuery({
    queryKey: queryKeys.forecast.inventory(productId),
    queryFn: () => forecastService.getInventoryRecommendations(productId),
    enabled: !!productId,
    staleTime: 600000, // 10 minutes
  });
};

/**
 * Hook to fetch forecast accuracy metrics
 */
export const useForecastAccuracy = (productId, timeRange = '90d') => {
  return useQuery({
    queryKey: queryKeys.forecast.accuracy(productId, timeRange),
    queryFn: () => forecastService.getForecastAccuracy(productId, timeRange),
    enabled: !!productId,
    staleTime: 3600000, // 1 hour
  });
};

/**
 * Hook to fetch demand-supply gap analysis
 */
export const useDemandSupplyGap = (productId, horizon = '30d') => {
  return useQuery({
    queryKey: queryKeys.forecast.gap(productId, horizon),
    queryFn: () => forecastService.getDemandSupplyGap(productId, horizon),
    enabled: !!productId,
    staleTime: 600000, // 10 minutes
  });
};

/**
 * Hook to generate custom forecast
 */
export const useGenerateForecast = () => {
  return useMutation({
    mutationFn: (forecastParams) => forecastService.generateForecast(forecastParams),
  });
};

/**
 * Hook to adjust forecast parameters
 */
export const useAdjustForecast = () => {
  return useMutation({
    mutationFn: ({ productId, adjustments }) => 
      forecastService.adjustForecast(productId, adjustments),
  });
};
