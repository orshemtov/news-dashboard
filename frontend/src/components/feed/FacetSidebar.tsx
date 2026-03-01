import { useState } from 'react';
import type { FacetsResponse } from '@/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, X, Filter, Minus, Plus } from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface FacetFilters {
  sources_include: string[];
  sources_exclude: string[];
  languages_include: string[];
  languages_exclude: string[];
  forwarded?: boolean;
  exclude_keywords: string[];
}

export const EMPTY_FACET_FILTERS: FacetFilters = {
  sources_include: [],
  sources_exclude: [],
  languages_include: [],
  languages_exclude: [],
  forwarded: undefined,
  exclude_keywords: [],
};

interface FacetSidebarProps {
  facets: FacetsResponse | undefined;
  filters: FacetFilters;
  onChange: (filters: FacetFilters) => void;
  isLoading?: boolean;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

type FacetState = 'include' | 'exclude' | 'none';

function getFacetState(
  value: string,
  include: string[],
  exclude: string[],
): FacetState {
  if (include.includes(value)) return 'include';
  if (exclude.includes(value)) return 'exclude';
  return 'none';
}

function cycleFacetState(
  value: string,
  include: string[],
  exclude: string[],
): { include: string[]; exclude: string[] } {
  const state = getFacetState(value, include, exclude);
  // none -> include -> exclude -> none
  switch (state) {
    case 'none':
      return { include: [...include, value], exclude };
    case 'include':
      return {
        include: include.filter((v) => v !== value),
        exclude: [...exclude, value],
      };
    case 'exclude':
      return {
        include,
        exclude: exclude.filter((v) => v !== value),
      };
  }
}

// ---------------------------------------------------------------------------
// FacetSection: collapsible group of facet values
// ---------------------------------------------------------------------------

function FacetSection({
  title,
  items,
  include,
  exclude,
  onToggle,
}: {
  title: string;
  items: { value: string; count: number }[];
  include: string[];
  exclude: string[];
  onToggle: (value: string) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const hasActive = include.length > 0 || exclude.length > 0;

  if (items.length === 0) return null;

  return (
    <div className="space-y-1">
      <button
        onClick={() => setCollapsed((c) => !c)}
        className="flex w-full items-center gap-1 py-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70 hover:text-foreground"
      >
        {collapsed ? (
          <ChevronRight className="size-3" />
        ) : (
          <ChevronDown className="size-3" />
        )}
        {title}
        {hasActive && (
          <span className="ml-auto rounded-full bg-primary/15 px-1.5 text-[10px] font-medium text-primary">
            {include.length + exclude.length}
          </span>
        )}
      </button>

      {!collapsed && (
        <div className="space-y-0.5">
          {items.map(({ value, count }) => {
            const state = getFacetState(value, include, exclude);
            return (
              <button
                key={value}
                onClick={() => onToggle(value)}
                className={cn(
                  'flex w-full items-center gap-2 rounded px-1.5 py-1 text-xs transition-colors',
                  'hover:bg-accent/60',
                  state === 'include' && 'bg-primary/10 text-primary',
                  state === 'exclude' && 'bg-destructive/10 text-destructive',
                )}
              >
                <span
                  className={cn(
                    'flex size-3.5 shrink-0 items-center justify-center rounded-sm border',
                    state === 'include' && 'border-primary bg-primary text-primary-foreground',
                    state === 'exclude' && 'border-destructive bg-destructive text-white',
                    state === 'none' && 'border-border',
                  )}
                >
                  {state === 'include' && <Plus className="size-2.5" strokeWidth={3} />}
                  {state === 'exclude' && <Minus className="size-2.5" strokeWidth={3} />}
                </span>
                <span className="truncate">{value}</span>
                <span className="ml-auto shrink-0 tabular-nums text-muted-foreground/50">
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// FacetSidebar
// ---------------------------------------------------------------------------

export function FacetSidebar({
  facets,
  filters,
  onChange,
  isLoading,
}: FacetSidebarProps) {
  const [keywordInput, setKeywordInput] = useState('');

  const hasAnyFilter =
    filters.sources_include.length > 0 ||
    filters.sources_exclude.length > 0 ||
    filters.languages_include.length > 0 ||
    filters.languages_exclude.length > 0 ||
    filters.forwarded !== undefined ||
    filters.exclude_keywords.length > 0;

  const handleSourceToggle = (value: string) => {
    const { include, exclude } = cycleFacetState(
      value,
      filters.sources_include,
      filters.sources_exclude,
    );
    onChange({ ...filters, sources_include: include, sources_exclude: exclude });
  };

  const handleLanguageToggle = (value: string) => {
    const { include, exclude } = cycleFacetState(
      value,
      filters.languages_include,
      filters.languages_exclude,
    );
    onChange({
      ...filters,
      languages_include: include,
      languages_exclude: exclude,
    });
  };

  const handleForwardedToggle = (value: string) => {
    const boolVal = value === 'true';
    // Toggle: if already set to this value, clear it
    onChange({
      ...filters,
      forwarded: filters.forwarded === boolVal ? undefined : boolVal,
    });
  };

  const addKeyword = () => {
    const kw = keywordInput.trim();
    if (!kw || filters.exclude_keywords.includes(kw)) return;
    onChange({
      ...filters,
      exclude_keywords: [...filters.exclude_keywords, kw],
    });
    setKeywordInput('');
  };

  const removeKeyword = (kw: string) => {
    onChange({
      ...filters,
      exclude_keywords: filters.exclude_keywords.filter((k) => k !== kw),
    });
  };

  return (
    <div className="flex h-full flex-col border-r border-border/30 bg-card/30">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/30 px-3 py-2.5">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground/80">
          <Filter className="size-3.5" />
          Filters
        </div>
        {hasAnyFilter && (
          <Button
            variant="ghost"
            size="sm"
            className="h-5 px-1.5 text-[10px] text-muted-foreground hover:text-foreground"
            onClick={() => onChange(EMPTY_FACET_FILTERS)}
          >
            Clear all
          </Button>
        )}
      </div>

      {/* Scrollable facets */}
      <ScrollArea className="flex-1">
        <div className="space-y-4 p-3">
          {/* Sources */}
          <FacetSection
            title="Source"
            items={facets?.sources ?? []}
            include={filters.sources_include}
            exclude={filters.sources_exclude}
            onToggle={handleSourceToggle}
          />

          {/* Languages */}
          <FacetSection
            title="Language"
            items={facets?.languages ?? []}
            include={filters.languages_include}
            exclude={filters.languages_exclude}
            onToggle={handleLanguageToggle}
          />

          {/* Forwarded */}
          {facets?.forwarded && facets.forwarded.length > 0 && (
            <div className="space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                Forwarded
              </span>
              <div className="space-y-0.5">
                {facets.forwarded.map(({ value, count }) => {
                  const isActive = filters.forwarded === (value === 'true');
                  return (
                    <button
                      key={value}
                      onClick={() => handleForwardedToggle(value)}
                      className={cn(
                        'flex w-full items-center gap-2 rounded px-1.5 py-1 text-xs transition-colors',
                        'hover:bg-accent/60',
                        isActive && 'bg-primary/10 text-primary',
                      )}
                    >
                      <span
                        className={cn(
                          'flex size-3.5 shrink-0 items-center justify-center rounded-sm border',
                          isActive
                            ? 'border-primary bg-primary text-primary-foreground'
                            : 'border-border',
                        )}
                      >
                        {isActive && <Plus className="size-2.5" strokeWidth={3} />}
                      </span>
                      <span>{value === 'true' ? 'Yes' : 'No'}</span>
                      <span className="ml-auto tabular-nums text-muted-foreground/50">
                        {count}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Keyword Exclusion */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
              Exclude keywords
            </span>
            <div className="flex gap-1">
              <Input
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addKeyword();
                  }
                }}
                placeholder="keyword..."
                className="h-7 text-xs"
              />
              <Button
                variant="outline"
                size="sm"
                className="h-7 shrink-0 px-2 text-xs"
                onClick={addKeyword}
                disabled={!keywordInput.trim()}
              >
                Add
              </Button>
            </div>
            {filters.exclude_keywords.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {filters.exclude_keywords.map((kw) => (
                  <span
                    key={kw}
                    className="inline-flex items-center gap-0.5 rounded bg-destructive/10 px-1.5 py-0.5 text-[11px] text-destructive"
                  >
                    {kw}
                    <button
                      onClick={() => removeKeyword(kw)}
                      className="rounded-sm hover:bg-destructive/20"
                    >
                      <X className="size-2.5" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {isLoading && (
            <div className="py-4 text-center text-xs text-muted-foreground/50">
              Loading...
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
