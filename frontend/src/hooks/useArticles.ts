import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getArticles,
  getArticle,
  deleteArticle,
  type ArticleListParams,
} from '@/api/client';

export function useArticles(params?: ArticleListParams) {
  return useQuery({
    queryKey: ['articles', params],
    queryFn: () => getArticles(params),
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
