import { useQuery } from '@tanstack/react-query';
import { getFacets, type ArticleListParams } from '@/api/client';

export function useFacets(params?: Omit<ArticleListParams, 'page' | 'page_size'>) {
  return useQuery({
    queryKey: ['facets', params],
    queryFn: () => getFacets(params),
    // Refetch periodically so counts stay fresh with SSE updates
    refetchInterval: 30_000,
  });
}
