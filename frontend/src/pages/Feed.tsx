import { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useArticles } from '@/hooks/useArticles';
import { useArticleStream } from '@/hooks/useArticleStream';
import { useFacets } from '@/hooks/useFacets';
import { useSearch } from '@/hooks/useSearch';
import type { Article, SearchRequest } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Loader2,
  Activity,
  Plus,
  Search,
  X,
  ArrowUpDown,
  PanelLeftClose,
  PanelLeft,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ArticleCard } from '@/components/feed/ArticleCard';
import { ArticleDetailDialog } from '@/components/feed/ArticleDetailDialog';
import { StatsBar } from '@/components/feed/StatsBar';
import {
  FacetSidebar,
  EMPTY_FACET_FILTERS,
  type FacetFilters,
} from '@/components/feed/FacetSidebar';

// ---------------------------------------------------------------------------
// Time range presets (Datadog-style)
// ---------------------------------------------------------------------------

const TIME_RANGES = [
  { label: '1m', hours: 1 / 60 },
  { label: '5m', hours: 5 / 60 },
  { label: '15m', hours: 15 / 60 },
  { label: '30m', hours: 30 / 60 },
  { label: '1h', hours: 1 },
  { label: '4h', hours: 4 },
  { label: '12h', hours: 12 },
  { label: '1d', hours: 24 },
  { label: 'All', hours: 0 },
] as const;

type SortOption = 'newest' | 'oldest';

export default function Feed() {
  // SSE: auto-update when new articles arrive
  const { newIds, clearNewId } = useArticleStream();

  // Filters
  const [hideDuplicates, setHideDuplicates] = useState(true);
  const [timeRange, setTimeRange] = useState<number>(() => {
    const saved = localStorage.getItem('news-dashboard-time-range');
    if (saved !== null) {
      const parsed = Number(saved);
      if (!Number.isNaN(parsed)) return parsed;
    }
    return 0; // default: All
  });
  const [sortOrder, setSortOrder] = useState<SortOption>('newest');

  // Facet filters
  const [facetFilters, setFacetFilters] = useState<FacetFilters>(EMPTY_FACET_FILTERS);
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    // Default open on desktop, closed on mobile
    return typeof window !== 'undefined' && window.innerWidth >= 768;
  });

  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'keyword' | 'semantic' | 'hybrid'>('hybrid');
  const [isSearching, setIsSearching] = useState(false);

  // Article detail
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);

  // Compute time filter dates
  const fromDate = useMemo(() => {
    if (timeRange === 0) return undefined;
    const d = new Date(Date.now() - timeRange * 60 * 60 * 1000);
    return d.toISOString();
  }, [timeRange]);

  // Build article list params including facet filters
  const articleParams = useMemo(() => ({
    is_duplicate: hideDuplicates ? false : undefined,
    from_date: fromDate,
    to_date: undefined,
    ...(facetFilters.sources_include.length > 0 && {
      sources_include: facetFilters.sources_include,
    }),
    ...(facetFilters.sources_exclude.length > 0 && {
      sources_exclude: facetFilters.sources_exclude,
    }),
    ...(facetFilters.exclude_keywords.length > 0 && {
      exclude_keywords: facetFilters.exclude_keywords,
    }),
  }), [hideDuplicates, fromDate, facetFilters]);

  // Feed query (infinite scroll)
  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useArticles(articleParams);

  // Facets query — pass same filters so counts reflect current selection
  const { data: facets, isLoading: facetsLoading } = useFacets({
    ...articleParams,
  });

  // Search query
  const search = useSearch();

  const handleSearch = () => {
    const text = searchQuery.trim();
    if (!text) {
      setIsSearching(false);
      return;
    }
    setIsSearching(true);
    const request: SearchRequest = {
      query: text,
      mode: searchMode,
      from_date: fromDate,
      sources_include: facetFilters.sources_include.length > 0 ? facetFilters.sources_include : undefined,
      sources_exclude: facetFilters.sources_exclude.length > 0 ? facetFilters.sources_exclude : undefined,
      exclude_keywords: facetFilters.exclude_keywords.length > 0 ? facetFilters.exclude_keywords : undefined,
    };
    search.mutate(request);
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
    if (e.key === 'Escape') clearSearch();
  };

  const clearSearch = () => {
    setSearchQuery('');
    setIsSearching(false);
    search.reset();
  };

  // Flatten all pages into a single article list
  const feedArticles = useMemo(
    () => data?.pages.flatMap((p) => p.items) ?? [],
    [data],
  );
  const searchArticlesData = search.data?.items ?? [];
  const articles = isSearching ? searchArticlesData : feedArticles;
  const total = isSearching
    ? (search.data?.total ?? 0)
    : (data?.pages[0]?.total ?? 0);

  // Sort (search results come pre-ranked, only sort feed articles)
  const sortedArticles = useMemo(() => {
    if (isSearching) return articles; // search results are ranked by relevance
    return [...articles].sort((a, b) => {
      const aTime = new Date(a.published_at).getTime();
      const bTime = new Date(b.published_at).getTime();
      return sortOrder === 'newest' ? bTime - aTime : aTime - bTime;
    });
  }, [articles, sortOrder, isSearching]);

  // ---------------------------------------------------------------------------
  // Infinite scroll – IntersectionObserver on sentinel element
  // ---------------------------------------------------------------------------
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries;
      if (entry.isIntersecting && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
    [fetchNextPage, hasNextPage, isFetchingNextPage],
  );

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(handleObserver, {
      rootMargin: '200px', // trigger 200px before reaching the end
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [handleObserver]);

  // Count active facet filters for the toggle button badge
  const activeFacetCount =
    facetFilters.sources_include.length +
    facetFilters.sources_exclude.length +
    facetFilters.exclude_keywords.length;

  return (
    <div className="flex gap-0">
      {/* Facet Sidebar — always in DOM, width transitions to avoid layout jump */}
      <aside
        className={cn(
          'hidden shrink-0 overflow-hidden transition-all duration-200 md:block',
          sidebarOpen ? 'w-60' : 'w-0',
        )}
      >
        <div className="sticky top-16 h-[calc(100vh-4rem)] w-60">
          <FacetSidebar
            facets={facets}
            filters={facetFilters}
            onChange={setFacetFilters}
            isLoading={facetsLoading}
          />
        </div>
      </aside>

      {/* Main content */}
      <div className="min-w-0 flex-1 space-y-3">
        {/* Stats Bar */}
        <StatsBar />

        {/* Search Bar */}
        <div className="flex gap-2">
          {/* Sidebar toggle */}
          <Button
            variant="outline"
            size="sm"
            className="hidden h-9 shrink-0 px-2 md:flex"
            onClick={() => setSidebarOpen((o) => !o)}
            title={sidebarOpen ? 'Hide filters' : 'Show filters'}
          >
            {sidebarOpen ? (
              <PanelLeftClose className="size-4" />
            ) : (
              <PanelLeft className="size-4" />
            )}
            {!sidebarOpen && activeFacetCount > 0 && (
              <span className="ml-0.5 rounded-full bg-primary px-1.5 text-[10px] font-medium text-primary-foreground">
                {activeFacetCount}
              </span>
            )}
          </Button>

          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/60" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              placeholder="Search articles..."
              className="border-border/40 bg-card pl-9 pr-8"
            />
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="size-3.5" />
              </button>
            )}
          </div>
          <Button
            onClick={handleSearch}
            disabled={search.isPending || !searchQuery.trim()}
            size="sm"
            className="px-4"
          >
            {search.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              'Search'
            )}
          </Button>
        </div>

        {/* Search mode tabs (visible when searching) */}
        {(isSearching || searchQuery) && (
          <Tabs
            value={searchMode}
            onValueChange={(v) => setSearchMode(v as typeof searchMode)}
          >
            <TabsList className="h-8">
              <TabsTrigger value="keyword" className="text-xs">
                Keyword
              </TabsTrigger>
              <TabsTrigger value="semantic" className="text-xs">
                Semantic
              </TabsTrigger>
              <TabsTrigger value="hybrid" className="text-xs">
                Hybrid
              </TabsTrigger>
            </TabsList>
          </Tabs>
        )}

        {/* Filters */}
        <div className="flex flex-col gap-3 rounded-lg border border-border/30 bg-card/40 px-3 py-2 sm:flex-row sm:items-center">
          <div className="flex items-center gap-3 overflow-hidden">
            <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground/60 shrink-0">Time</span>
            <div className="flex overflow-x-auto rounded-md border border-border/40 no-scrollbar">
              {TIME_RANGES.map((tr) => (
                <button
                  key={tr.label}
                  onClick={() => {
                    setTimeRange(tr.hours);
                    localStorage.setItem('news-dashboard-time-range', String(tr.hours));
                  }}
                  className={cn(
                    'shrink-0 px-2.5 py-1 text-xs font-medium transition-colors',
                    timeRange === tr.hours
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground/70 hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  {tr.label}
                </button>
              ))}
            </div>
          </div>

          <div className="hidden h-4 w-px bg-border/50 sm:block" />

          <div className="flex flex-1 items-center gap-3 min-w-0">
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs shrink-0"
              onClick={() =>
                setSortOrder((s) => (s === 'newest' ? 'oldest' : 'newest'))
              }
            >
              <ArrowUpDown className="size-3" />
              {sortOrder === 'newest' ? 'Newest' : 'Oldest'}
            </Button>

            <label className="flex items-center gap-1.5 text-xs text-muted-foreground shrink-0">
              <input
                type="checkbox"
                checked={hideDuplicates}
                onChange={(e) => {
                  setHideDuplicates(e.target.checked);
                }}
                className="rounded border-input"
              />
              Hide dupes
            </label>

            <span className="ml-auto text-xs text-muted-foreground whitespace-nowrap">
              {total} article{total !== 1 ? 's' : ''}
              {isSearching && search.data
                ? ` for "${search.data.query}"`
                : ''}
            </span>
          </div>
        </div>

        {/* Loading (initial) */}
        {(isLoading || search.isPending) && (
          <div className="flex justify-center py-12">
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          </div>
        )}
        {(isError || search.isError) && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
            Failed to load articles. The backend may be unavailable.
          </div>
        )}

        {/* Empty State */}
        {!isLoading &&
          !isError &&
          !search.isPending &&
          sortedArticles.length === 0 &&
          total === 0 &&
          !isSearching && (
            <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
              <div className="rounded-full bg-muted p-4">
                <Activity className="size-8 text-muted-foreground" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">No articles yet</h3>
                <p className="max-w-sm text-sm text-muted-foreground">
                  Add Telegram channels to start ingesting articles from the
                  Sources page.
                </p>
              </div>
              <Button asChild>
                <Link to="/sources">
                  <Plus className="size-4" />
                  Add Sources
                </Link>
              </Button>
            </div>
          )}

        {/* Search empty state */}
        {isSearching &&
          !search.isPending &&
          search.data &&
          searchArticlesData.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
              <Search className="mb-3 size-10 opacity-20" />
              <p className="text-sm">No results found for "{search.data.query}"</p>
            </div>
          )}

        {/* Article Cards */}
        <div className="mx-auto grid max-w-3xl gap-3">
          {sortedArticles.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              onClick={() => setSelectedArticle(article)}
              isNew={newIds.has(article.id)}
              onAnimationEnd={() => clearNewId(article.id)}
            />
          ))}
        </div>

        {/* Infinite scroll sentinel */}
        {!isSearching && (
          <div ref={sentinelRef} className="flex justify-center py-4">
            {isFetchingNextPage && (
              <Loader2 className="size-5 animate-spin text-muted-foreground" />
            )}
            {!hasNextPage && sortedArticles.length > 0 && (
              <span className="text-xs text-muted-foreground/50">
                End of feed
              </span>
            )}
          </div>
        )}

        {/* Article Detail Dialog */}
        <ArticleDetailDialog
          article={selectedArticle}
          onClose={() => setSelectedArticle(null)}
        />
      </div>
    </div>
  );
}
