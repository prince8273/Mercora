import { useMutation, useQuery as useReactQuery } from '@tanstack/react-query';
import { queryService } from '../services/queryService';
import { queryKeys } from '../lib/queryClient';

/**
 * Hook to fetch query history
 */
export const useQueryHistory = (filters = {}) => {
  return useReactQuery({
    queryKey: queryKeys.queries.list(filters),
    queryFn: () => queryService.getQueryHistory(filters),
    staleTime: 30000, // 30 seconds
  });
};

/**
 * Hook to fetch a single query by ID
 */
export const useQueryById = (queryId) => {
  return useReactQuery({
    queryKey: queryKeys.queries.detail(queryId),
    queryFn: () => queryService.getQueryById(queryId),
    enabled: !!queryId,
  });
};

/**
 * Hook to execute a natural language query
 */
export const useExecuteQuery = () => {
  return useMutation({
    mutationFn: (queryData) => queryService.executeQuery(queryData),
  });
};

/**
 * Hook to get query suggestions
 */
export const useQuerySuggestions = (input) => {
  return useReactQuery({
    queryKey: queryKeys.queries.suggestions(input),
    queryFn: () => queryService.getQuerySuggestions(input),
    enabled: input?.length > 2,
    staleTime: 60000, // 1 minute
  });
};

/**
 * Hook to cancel a running query
 */
export const useCancelQuery = () => {
  return useMutation({
    mutationFn: (queryId) => queryService.cancelQuery(queryId),
  });
};

/**
 * Hook to export query results
 */
export const useExportResults = () => {
  return useMutation({
    mutationFn: ({ queryId, format }) => queryService.exportResults(queryId, format),
  });
};
