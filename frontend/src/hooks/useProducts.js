import { useQuery } from '@tanstack/react-query';
import { productService } from '../services/productService';
import { queryKeys } from '../lib/queryClient';

/**
 * Hook to fetch all products
 */
export const useProducts = (params = {}) => {
  return useQuery({
    queryKey: queryKeys.products.list(params),
    queryFn: () => productService.getProducts(params),
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook to fetch a single product
 */
export const useProduct = (productId) => {
  return useQuery({
    queryKey: queryKeys.products.detail(productId),
    queryFn: () => productService.getProduct(productId),
    enabled: !!productId,
    staleTime: 300000, // 5 minutes
  });
};
