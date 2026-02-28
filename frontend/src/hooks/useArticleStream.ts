import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';

/**
 * Subscribes to the SSE endpoint at /api/articles/stream.
 * When a "new_articles" event arrives, invalidates the articles query
 * so React Query refetches automatically.
 */
export function useArticleStream() {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = new EventSource('/api/articles/stream');
    eventSourceRef.current = es;

    es.addEventListener('new_articles', () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    });

    es.onerror = () => {
      // EventSource auto-reconnects on error; nothing extra needed.
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [queryClient]);
}
