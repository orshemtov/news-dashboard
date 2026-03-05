import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient, type InfiniteData } from '@tanstack/react-query';
import type { Article, ArticleListResponse } from '@/types';

/**
 * Subscribes to the SSE endpoint at /api/articles/stream.
 * When a "new_articles" event arrives, prepends the full article data
 * directly into the React Query infinite cache — no refetch needed.
 *
 * Returns a Set of article IDs that arrived via SSE (for entrance
 * animations) and a callback to clear an ID once the animation ends.
 */
export function useArticleStream() {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);
  const [newIds, setNewIds] = useState<Set<string>>(() => new Set());
  const [burst, setBurst] = useState<{
    id: string;
    lead_article: Article;
    sources: string[];
    count: number;
    timestamp: string;
  } | null>(null);

  const clearNewId = useCallback((id: string) => {
    setNewIds((prev) => {
      if (!prev.has(id)) return prev;
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }, []);

  const clearBurst = useCallback(() => setBurst(null), []);

  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_BASE_URL ?? '/api';
    const es = new EventSource(`${apiBase}/articles/stream`);
    eventSourceRef.current = es;

    es.addEventListener('burst', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        setBurst({
          id: data.cluster_id,
          lead_article: data.lead_article,
          sources: data.sources,
          count: data.count,
          timestamp: data.timestamp,
        });
      } catch (err) {
        console.error('Failed to parse burst event', err);
      }
    });

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

      // Prepend new articles into the first page of every cached infinite query
      queryClient.setQueriesData<InfiniteData<ArticleListResponse>>(
        { queryKey: ['articles'] },
        (old) => {
          if (!old || !old.pages.length) return old;

          const firstPage = old.pages[0];

          // Deduplicate: collect all existing IDs across all pages
          const existingIds = new Set(
            old.pages.flatMap((p) => p.items.map((a) => a.id)),
          );
          const newItems = articles.filter((a) => !existingIds.has(a.id));
          if (newItems.length === 0) return old;

          // Prepend to the first page
          const updatedFirstPage: ArticleListResponse = {
            ...firstPage,
            items: [...newItems, ...firstPage.items],
            total: firstPage.total + newItems.length,
          };

          // Update total in all pages so pagination calculates correctly
          const updatedPages = old.pages.map((p, i) =>
            i === 0
              ? updatedFirstPage
              : { ...p, total: p.total + newItems.length },
          );

          return {
            ...old,
            pages: updatedPages,
          };
        },
      );
    });

    es.onerror = (err) => {
      console.error('SSE Connection Error:', err);
      // EventSource auto-reconnects on error; but we log it to see if it's failing
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [queryClient]);

  return { newIds, clearNewId, burst, clearBurst };
}
