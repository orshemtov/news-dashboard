import {
  useQuery,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import {
  getArticles,
  getArticle,
  deleteArticle,
  type ArticleListParams,
} from '@/api/client';
import type { ArticleListResponse } from '@/types';

const PAGE_SIZE = 20;

export function useArticles(params?: Omit<ArticleListParams, 'page' | 'page_size'>) {
  return useInfiniteQuery<ArticleListResponse>({
    queryKey: ['articles', params],
    queryFn: ({ pageParam }) =>
      getArticles({ ...params, page: pageParam as number, page_size: PAGE_SIZE }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const totalPages = Math.ceil(lastPage.total / PAGE_SIZE);
      return lastPage.page < totalPages ? lastPage.page + 1 : undefined;
    },
    refetchInterval: 30000, // Refetch every 30 seconds as a fallback for SSE
  });
}

export function useArticle(id: string) {
  return useQuery({
    queryKey: ['articles', id],
    queryFn: () => getArticle(id),
    enabled: !!id,
  });
}

export function useDeleteArticle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteArticle(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
}
