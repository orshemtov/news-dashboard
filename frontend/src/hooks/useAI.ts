import { useMutation } from '@tanstack/react-query';
import { summarizeArticle, translateArticle } from '@/api/client';

export function useSummarize() {
  return useMutation({
    mutationFn: (articleId: string) => summarizeArticle(articleId),
  });
}

export function useTranslate() {
  return useMutation({
    mutationFn: ({
      articleId,
      targetLanguage,
    }: {
      articleId: string;
      targetLanguage: string;
    }) => translateArticle(articleId, targetLanguage),
  });
}
