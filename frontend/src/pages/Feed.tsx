import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useArticles } from '@/hooks/useArticles';
import { useSearch } from '@/hooks/useSearch';
import type { Article, SearchRequest } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ChevronLeft,
  ChevronRight,
  Loader2,
  Newspaper,
  Plus,
  Search,
  X,
  ArrowUpDown,
} from 'lucide-react';
import { ArticleCard } from '@/components/feed/ArticleCard';
import { ArticleDetailDialog } from '@/components/feed/ArticleDetailDialog';
import { StatsBar } from '@/components/feed/StatsBar';
import { ChatPanel } from '@/components/chat/ChatPanel';

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
  { label: '3d', hours: 72 },
  { label: '7d', hours: 168 },
  { label: '30d', hours: 720 },
  { label: 'All', hours: 0 },
] as const;

// ---------------------------------------------------------------------------
// Refresh interval presets
// ---------------------------------------------------------------------------

const REFRESH_INTERVALS = [
  { label: '5s', ms: 5_000 },
  { label: '10s', ms: 10_000 },
  { label: '30s', ms: 30_000 },
  { label: '1m', ms: 60_000 },
  { label: '5m', ms: 300_000 },
  { label: 'Off', ms: 0 },
] as const;

type SortOption = 'newest' | 'oldest';

export default function Feed() {
  // Filters
  const [page, setPage] = useState(1);
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
  const [refreshInterval, setRefreshInterval] = useState<number>(() => {
    const saved = localStorage.getItem('news-dashboard-refresh-interval');
    if (saved !== null) {
      const parsed = Number(saved);
      if (!Number.isNaN(parsed)) return parsed;
    }
    return 10_000; // default: 10s
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

  // Feed query (when not searching)
  const { data, isLoading, isError } = useArticles({
    page,
    page_size: 20,
    is_duplicate: hideDuplicates ? false : undefined,
    from_date: fromDate,
    to_date: undefined,
  }, refreshInterval || false);

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

  // Determine which articles to show
  const feedArticles = data?.items ?? [];
  const searchArticles = search.data?.items ?? [];
  const articles = isSearching ? searchArticles : feedArticles;
  const total = isSearching ? (search.data?.total ?? 0) : (data?.total ?? 0);
  const totalPages = isSearching ? 1 : Math.ceil(total / 20);

  // Sort (search results come pre-ranked, only sort feed articles)
  const sortedArticles = useMemo(() => {
    if (isSearching) return articles; // search results are ranked by relevance
    return [...articles].sort((a, b) => {
      const aTime = new Date(a.published_at).getTime();
      const bTime = new Date(b.published_at).getTime();
      return sortOrder === 'newest' ? bTime - aTime : aTime - bTime;
    });
  }, [articles, sortOrder, isSearching]);

  const resetPage = () => setPage(1);

  return (
    <div className="space-y-4">
      {/* Stats Bar */}
      <StatsBar />

      {/* Search Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            placeholder="Search articles..."
            className="pl-9 pr-8"
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
      <div className="space-y-3 rounded-lg border border-border/40 bg-card/50 p-3">
        {/* Row 1: Time Range */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">Time</span>
          <div className="flex rounded-md border border-input">
            {TIME_RANGES.map((tr) => (
              <button
                key={tr.label}
                onClick={() => {
                  setTimeRange(tr.hours);
                  localStorage.setItem('news-dashboard-time-range', String(tr.hours));
                  resetPage();
                }}
                className={`px-2 py-1 text-xs font-medium transition-colors first:rounded-l-md last:rounded-r-md ${
                  timeRange === tr.hours
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                }`}
              >
                {tr.label}
              </button>
            ))}
          </div>
        </div>

        {/* Row 2: Refresh + Sort + Dedup + Count */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground">Refresh</span>
            <div className="flex rounded-md border border-input">
              {REFRESH_INTERVALS.map((ri) => (
                <button
                  key={ri.label}
                  onClick={() => {
                    setRefreshInterval(ri.ms);
                    localStorage.setItem('news-dashboard-refresh-interval', String(ri.ms));
                  }}
                  className={`px-2 py-1 text-xs font-medium transition-colors first:rounded-l-md last:rounded-r-md ${
                    refreshInterval === ri.ms
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  }`}
                >
                  {ri.label}
                </button>
              ))}
            </div>
          </div>

          <div className="h-4 w-px bg-border" />

          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            onClick={() =>
              setSortOrder((s) => (s === 'newest' ? 'oldest' : 'newest'))
            }
          >
            <ArrowUpDown className="size-3" />
            {sortOrder === 'newest' ? 'Newest' : 'Oldest'}
          </Button>

          <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={hideDuplicates}
              onChange={(e) => {
                setHideDuplicates(e.target.checked);
                resetPage();
              }}
              className="rounded border-input"
            />
            Hide dupes
          </label>

          <span className="ml-auto text-xs text-muted-foreground">
            {total} article{total !== 1 ? 's' : ''}
            {isSearching && search.data
              ? ` for "${search.data.query}" (${search.data.mode})`
              : ''}
          </span>
        </div>
      </div>

      {/* Loading / Error */}
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
              <Newspaper className="size-8 text-muted-foreground" />
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
        searchArticles.length === 0 && (
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
          />
        ))}
      </div>

      {/* Pagination (only for feed, not search) */}
      {!isSearching && totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pb-4">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="size-4" />
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}

      {/* Article Detail Dialog */}
      <ArticleDetailDialog
        article={selectedArticle}
        onClose={() => setSelectedArticle(null)}
      />

      {/* Floating Chat Panel */}
      <ChatPanel />
    </div>
  );
}
