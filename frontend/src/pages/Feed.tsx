import { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useArticles } from '@/hooks/useArticles';
import { useArticleStream } from '@/hooks/useArticleStream';
import { useFacets } from '@/hooks/useFacets';
import { useSearch } from '@/hooks/useSearch';
import type { Article, SearchRequest } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Loader2,
  Activity,
  Plus,
  Search,
  X,
  EyeOff,
  Eye,
  ArrowUpDown,
  ArrowUp,
  PanelLeftClose,
  PanelLeft,
  Filter,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ArticleCard } from '@/components/feed/ArticleCard';
import { hideArticle, unhideArticle } from '@/api/client';
import { useQueryClient } from '@tanstack/react-query';
import { BreakingBar } from '@/components/feed/BreakingBar';
import { StatsBar } from '@/components/feed/StatsBar';
import { TrendingThemes } from '@/components/feed/TrendingThemes';
import {
  FacetSidebar,
  EMPTY_FACET_FILTERS,
  type FacetFilters,
} from '@/components/feed/FacetSidebar';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

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

// Deterministic accent color from source name
const SOURCE_COLORS = [
  'bg-violet-500', 'bg-indigo-500', 'bg-purple-500', 'bg-fuchsia-500',
  'bg-blue-500', 'bg-cyan-500', 'bg-teal-500', 'bg-emerald-500',
  'bg-rose-500', 'bg-amber-500', 'bg-pink-500', 'bg-slate-500',
];

function sourceColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return SOURCE_COLORS[Math.abs(hash) % SOURCE_COLORS.length];
}

export default function Feed() {
  const queryClient = useQueryClient();
  // SSE: auto-update when new articles arrive
  const { newIds, clearNewId, burst, clearBurst } = useArticleStream();

  // Filters
  const [hideDuplicates, setHideDuplicates] = useState(true);
  const [showHiddenOnly, setShowHiddenOnly] = useState(false);
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
  const [isSearching, setIsSearching] = useState(false);
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);

  // Back to top visibility
  const [showBackToTop, setShowBackToTop] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setShowBackToTop(window.scrollY > 500);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Compute time filter dates
  const fromDate = useMemo(() => {
    if (timeRange === 0) return undefined;
    const d = new Date(Date.now() - timeRange * 60 * 60 * 1000);
    return d.toISOString();
  }, [timeRange]);

  // Build article list params including facet filters
  const articleParams = useMemo(() => ({
    is_duplicate: hideDuplicates ? false : undefined,
    include_hidden: showHiddenOnly,
    from_date: fromDate,
    to_date: undefined,
    ...(selectedClusterId && { dedup_cluster_id: selectedClusterId }),
    ...(facetFilters.sources_include.length > 0 && {
      sources_include: facetFilters.sources_include,
    }),
    ...(facetFilters.sources_exclude.length > 0 && {
      sources_exclude: facetFilters.sources_exclude,
    }),
    ...(facetFilters.exclude_keywords.length > 0 && {
      exclude_keywords: facetFilters.exclude_keywords,
    }),
  }), [hideDuplicates, showHiddenOnly, fromDate, selectedClusterId, facetFilters]);

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
      mode: 'hybrid',
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

  const handleHideArticle = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      if (showHiddenOnly) {
        await unhideArticle(id);
      } else {
        await hideArticle(id);
      }
      // Optimistically invalidate and refetch, or just wait for SSE if implemented for hide
      // For now, manual invalidate is safer
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      queryClient.invalidateQueries({ queryKey: ['facets'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    } catch (err) {
      console.error('Failed to update article visibility:', err);
    }
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

  // 1. Group articles by dedup_hash (Visual Clustering)
  const groupedArticles = useMemo(() => {
    const groups: Record<string, Article[]> = {};
    const singles: Article[] = [];

    sortedArticles.forEach((article) => {
      if (hideDuplicates && article.dedup_hash) {
        if (!groups[article.dedup_hash]) {
          groups[article.dedup_hash] = [];
        }
        groups[article.dedup_hash].push(article);
      } else {
        singles.push(article);
      }
    });

    // For each group, pick the "best" one as lead, or just first
    const result: { lead: Article; variations: Article[] }[] = [];
    
    // Handle singles first
    singles.forEach(a => result.push({ lead: a, variations: [] }));

    // Handle groups
    if (hideDuplicates) {
      Object.values(groups).forEach(group => {
        // Sort group by has_media, then by content length
        const sortedGroup = [...group].sort((a, b) => {
          const aMedia = (a.media_attachments?.length ?? 0) > 0 ? 1 : 0;
          const bMedia = (b.media_attachments?.length ?? 0) > 0 ? 1 : 0;
          if (aMedia !== bMedia) return bMedia - aMedia;
          return (b.content?.length ?? 0) - (a.content?.length ?? 0);
        });
        result.push({ lead: sortedGroup[0], variations: sortedGroup.slice(1) });
      });

      // Sort result by lead's published_at to maintain feed order
      return result.sort((a, b) => {
        const aTime = new Date(a.lead.published_at).getTime();
        const bTime = new Date(b.lead.published_at).getTime();
        return sortOrder === 'newest' ? bTime - aTime : aTime - bTime;
      });
    }

    return result;
  }, [sortedArticles, hideDuplicates, sortOrder]);

  return (
    <div className="flex gap-4">
      {/* Facet Sidebar — always in DOM, width transitions to avoid layout jump */}
      <aside
        className={cn(
          'hidden shrink-0 transition-all duration-200 md:block',
          sidebarOpen ? 'w-60' : 'w-0',
        )}
      >
        <div className="sticky top-16 h-[calc(100vh-4rem)]">
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
        {/* Breaking Bar */}
        {burst && (
          <BreakingBar 
            burst={burst} 
            onClose={clearBurst} 
            onClick={() => {
              if (burst.lead_article.url) {
                window.open(burst.lead_article.url, '_blank', 'noopener,noreferrer');
              }
            }} 
          />
        )}

        {/* Stats Bar */}
        <StatsBar />

        {/* Trending Themes (Mobile/Tablet) */}
        <div className="lg:hidden">
          <TrendingThemes
            sticky={false}
            onThemeClick={(clusterId) => {
              setSelectedClusterId(clusterId);
              setHideDuplicates(false);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
          />
        </div>

        {/* Search Bar */}
        <div className="flex gap-2">
          {/* Sidebar toggle (Desktop) */}
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

          {/* Sidebar Drawer (Mobile) */}
          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="relative h-9 shrink-0 px-2 md:hidden"
                title="Filters"
              >
                <Filter className="size-4" />
                {activeFacetCount > 0 && (
                  <span className="absolute -right-1 -top-1 flex size-4 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground">
                    {activeFacetCount}
                  </span>
                )}
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-80 p-0">
              <SheetHeader className="px-4 py-2 border-b">
                <SheetTitle className="text-sm font-semibold uppercase tracking-wider">Filters</SheetTitle>
              </SheetHeader>
              <div className="h-[calc(100vh-4rem)]">
                <FacetSidebar
                  facets={facets}
                  filters={facetFilters}
                  onChange={setFacetFilters}
                  isLoading={facetsLoading}
                />
              </div>
            </SheetContent>
          </Sheet>

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

            <label className="flex items-center gap-1.5 text-xs text-muted-foreground shrink-0">
              <input
                type="checkbox"
                checked={showHiddenOnly}
                onChange={(e) => {
                  setShowHiddenOnly(e.target.checked);
                }}
                className="rounded border-input"
              />
              Show hidden only
            </label>

            {isSearching && search.data && (
              <span className="ml-auto text-xs text-muted-foreground whitespace-nowrap">
                Results for "{search.data.query}"
              </span>
            )}
          </div>
        </div>

        {selectedClusterId && (
          <div className="flex items-center gap-2 rounded-lg border border-orange-500/30 bg-orange-500/10 px-3 py-2 text-xs">
            <span className="font-medium text-orange-600">Theme filter active</span>
            <span className="truncate text-muted-foreground">Showing articles for selected trending theme</span>
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto h-7 px-2 text-xs"
              onClick={() => setSelectedClusterId(null)}
            >
              Clear
            </Button>
          </div>
        )}

        <div className="flex items-start gap-4">
          <div className="min-w-0 flex-1">
            {/* Loading (initial) */}
            {((isLoading && !data) || search.isPending) && (
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
        <div className="grid gap-3">
          {groupedArticles.map(({ lead, variations }) => (
            <div key={lead.id} className="space-y-1">
              <ArticleCard
                article={lead}
                onHide={(e) => handleHideArticle(lead.id, e)}
                isNew={newIds.has(lead.id)}
                isTrending={variations.length > 0}
                trendCount={variations.length + 1}
                isHiddenOnlyMode={showHiddenOnly}
                onAnimationEnd={() => clearNewId(lead.id)}
              />
              {variations.length > 0 && (
                <div className="flex flex-wrap gap-2 px-4 py-1">
                  <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground/50 self-center">
                    Also from:
                  </span>
                    {variations.map((v) => (
                      <div key={v.id} className="group/variation relative flex items-center">
                        <button
                          onClick={() => {
                            if (v.url) {
                              window.open(v.url, '_blank', 'noopener,noreferrer');
                            }
                          }}
                          className="inline-flex items-center gap-1 rounded-full border border-border/40 bg-card/40 px-2 py-0.5 text-[11px] font-medium text-muted-foreground hover:border-primary/30 hover:bg-accent/50 hover:text-foreground transition-all pr-5"
                        >
                          <span className={cn('size-1.5 shrink-0 rounded-full', sourceColor(v.source_name))} />
                          {v.source_name}
                        </button>
                        <button
                          onClick={(e) => handleHideArticle(v.id, e)}
                          className="absolute right-1 text-muted-foreground/0 group-variation:text-muted-foreground hover:!text-destructive transition-all"
                          title={showHiddenOnly ? "Unhide variation" : "Hide variation"}
                        >
                          {showHiddenOnly ? <Eye className="size-2.5" /> : <EyeOff className="size-2.5" />}
                        </button>
                      </div>
                    ))}
                </div>
              )}
            </div>
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
          </div>
          {/* Trending Themes Sidebar (Right) */}
          <aside className="hidden w-72 shrink-0 self-start lg:block xl:w-80">
            <TrendingThemes
              onThemeClick={(clusterId) => {
                setSelectedClusterId(clusterId);
                setHideDuplicates(false);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            />
          </aside>
        </div>

        {/* Back to top button */}
        <Button
          variant="secondary"
          size="icon"
          className={cn(
            'fixed bottom-20 right-6 z-50 rounded-full shadow-lg transition-all duration-300 md:bottom-8',
            showBackToTop ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0 pointer-events-none'
          )}
          onClick={scrollToTop}
          title="Back to top"
        >
          <ArrowUp className="size-5" />
        </Button>
      </div>
    </div>
  );
}
