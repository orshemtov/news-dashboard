import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Article, ArticleListResponse } from '@/types';

/**
 * Subscribes to the SSE endpoint at /api/articles/stream.
 * When a "new_articles" event arrives, prepends the full article data
 * directly into the React Query cache — no refetch needed.
 *
 * Returns a Set of article IDs that arrived via SSE (for entrance
 * animations) and a callback to clear an ID once the animation ends.
 */
export function useArticleStream() {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);
  const [newIds, setNewIds] = useState<Set<string>>(() => new Set());

  const clearNewId = useCallback((id: string) => {
    setNewIds((prev) => {
      if (!prev.has(id)) return prev;
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }, []);

  useEffect(() => {
    const es = new EventSource('/api/articles/stream');
    eventSourceRef.current = es;

    es.addEventListener('new_articles', (event: MessageEvent) => {
      let articles: Article[];
      try {
        const data = JSON.parse(event.data);
        articles = data.articles;
      } catch {
        return;
      }

      if (!articles || articles.length === 0) return;

      // Track these IDs as "new" for entrance animation
      setNewIds((prev) => {
        const next = new Set(prev);
        for (const a of articles) next.add(a.id);
        return next;
      });

      // Prepend new articles into every cached ArticleListResponse
      queryClient.setQueriesData<ArticleListResponse>(
        { queryKey: ['articles'] },
        (old) => {
          if (!old) return old;

          // Deduplicate: skip articles already in cache
          const existingIds = new Set(old.items.map((a) => a.id));
          const newItems = articles.filter((a) => !existingIds.has(a.id));
          if (newItems.length === 0) return old;

          return {
            ...old,
            items: [...newItems, ...old.items],
            total: old.total + newItems.length,
          };
        },
      );
    });

    es.onerror = () => {
      // EventSource auto-reconnects on error; nothing extra needed.
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [queryClient]);

  return { newIds, clearNewId };
}
