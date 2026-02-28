import { useMutation } from '@tanstack/react-query';
import { searchArticles } from '@/api/client';

export function useSearch() {
  return useMutation({
    mutationFn: searchArticles,
  });
}
