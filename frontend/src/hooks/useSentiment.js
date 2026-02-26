import { useQuery } from '@tanstack/react-query';
import { sentimentService } from '../services/sentimentService';
import { queryKeys } from '../lib/queryClient';

/**
 * Hook to fetch sentiment overview
 */
export const useSentimentOverview = (productId, filters = {}) => {
  return useQuery({
    queryKey: queryKeys.sentiment.overview(productId, filters),
    queryFn: () => sentimentService.getSentimentOverview(productId, filters),
    enabled: !!productId,
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook to fetch sentiment trends
 */
export const useSentimentTrends = (productId, timeRange = '30d') => {
  return useQuery({
    queryKey: queryKeys.sentiment.trends(productId, timeRange),
    queryFn: () => sentimentService.getSentimentTrends(productId, timeRange),
    enabled: !!productId,
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook to fetch theme breakdown
 */
export const useThemeBreakdown = (productId, filters = {}) => {
  return useQuery({
    queryKey: queryKeys.sentiment.themes(productId, filters),
    queryFn: () => sentimentService.getThemeBreakdown(productId, filters),
    enabled: !!productId,
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook to fetch reviews
 */
export const useReviews = (productId, filters = {}) => {
  return useQuery({
    queryKey: queryKeys.sentiment.reviews(productId, filters),
    queryFn: () => sentimentService.getReviews(productId, filters),
    enabled: !!productId,
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook to fetch feature requests
 */
export const useFeatureRequests = (productId, filters = {}) => {
  return useQuery({
    queryKey: queryKeys.sentiment.features(productId, filters),
    queryFn: () => sentimentService.getFeatureRequests(productId, filters),
    enabled: !!productId,
    staleTime: 600000, // 10 minutes
  });
};

/**
 * Hook to fetch complaint analysis
 */
export const useComplaintAnalysis = (productId, filters = {}) => {
  return useQuery({
    queryKey: queryKeys.sentiment.complaints(productId, filters),
    queryFn: () => sentimentService.getComplaintAnalysis(productId, filters),
    enabled: !!productId,
    staleTime: 300000, // 5 minutes
  });
};
