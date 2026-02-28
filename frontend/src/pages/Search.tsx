import { useState } from 'react';
import { useSearch } from '@/hooks/useSearch';
import { useSummarize, useTranslate } from '@/hooks/useAI';
import type { Article, SearchRequest } from '@/types';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Search as SearchIcon,
  Loader2,
  Sparkles,
  Languages,
  ExternalLink,
} from 'lucide-react';

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function Search() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<'keyword' | 'semantic' | 'hybrid'>(
    'hybrid'
  );
  const [sourceType, setSourceType] = useState<string>('');
  const [language, setLanguage] = useState<string>('');
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);

  const search = useSearch();
  const summarize = useSummarize();
  const translate = useTranslate();

  const handleSearch = () => {
    const text = query.trim();
    if (!text) return;

    const request: SearchRequest = {
      query: text,
      mode,
      source_types: sourceType ? [sourceType] : undefined,
      language: language || undefined,
    };
    search.mutate(request);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  const results = search.data?.items ?? [];

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <div className="space-y-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search articles..."
              className="pl-9"
            />
          </div>
          <Button onClick={handleSearch} disabled={search.isPending}>
            {search.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              'Search'
            )}
          </Button>
        </div>

        {/* Mode Tabs */}
        <Tabs
          value={mode}
          onValueChange={(v) => setMode(v as typeof mode)}
        >
          <TabsList>
            <TabsTrigger value="keyword">Keyword</TabsTrigger>
            <TabsTrigger value="semantic">Semantic</TabsTrigger>
            <TabsTrigger value="hybrid">Hybrid</TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All Sources</option>
            <option value="rss">RSS</option>
            <option value="telegram">Telegram</option>
          </select>

          <Input
            placeholder="Language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-32"
          />
        </div>
      </div>

      {/* Results */}
      {search.data && (
        <p className="text-sm text-muted-foreground">
          {search.data.total} results for &ldquo;{search.data.query}&rdquo; ({search.data.mode})
        </p>
      )}

      <div className="grid gap-3">
        {results.map((article) => (
          <Card
            key={article.id}
            className="cursor-pointer py-4 transition-colors hover:bg-accent/50"
            onClick={() => setSelectedArticle(article)}
          >
            <CardHeader className="pb-0">
              <div className="flex items-start justify-between gap-4">
                <CardTitle className="text-base leading-snug">
                  {article.title || article.content.slice(0, 120) + '...'}
                </CardTitle>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {timeAgo(article.published_at)}
                </span>
              </div>
            </CardHeader>
            <CardContent className="pt-2">
              {article.title && (
                <p className="mb-2 line-clamp-2 text-sm text-muted-foreground">
                  {article.content.slice(0, 200)}
                </p>
              )}
              <div className="flex items-center gap-2">
                <Badge variant="secondary">{article.source_name}</Badge>
                <Badge variant="outline">{article.source_type}</Badge>
                {article.language && (
                  <Badge variant="outline">{article.language}</Badge>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {!search.data && !search.isPending && (
        <div className="flex flex-col items-center justify-center py-16 text-center text-muted-foreground">
          <SearchIcon className="mb-4 size-12 opacity-20" />
          <p>Search across all collected news articles</p>
          <p className="text-sm">
            Use keyword, semantic, or hybrid search modes
          </p>
        </div>
      )}

      {/* Article Detail Dialog */}
      <Dialog
        open={!!selectedArticle}
        onOpenChange={(open) => !open && setSelectedArticle(null)}
      >
        {selectedArticle && (
          <DialogContent className="max-h-[85vh] sm:max-w-2xl">
            <DialogHeader>
              <DialogTitle>
                {selectedArticle.title || 'Article Detail'}
              </DialogTitle>
              <DialogDescription>
                <span className="flex items-center gap-2">
                  <Badge variant="secondary">
                    {selectedArticle.source_name}
                  </Badge>
                  <span className="text-xs">
                    {new Date(selectedArticle.published_at).toLocaleString()}
                  </span>
                </span>
              </DialogDescription>
            </DialogHeader>

            <ScrollArea className="max-h-[50vh]">
              <div className="space-y-4 pr-4">
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {selectedArticle.content}
                </p>

                {summarize.data &&
                  summarize.data.article_id === selectedArticle.id && (
                    <>
                      <Separator />
                      <div>
                        <h4 className="mb-1 text-sm font-semibold">
                          AI Summary
                        </h4>
                        <p className="text-sm text-muted-foreground">
                          {summarize.data.summary}
                        </p>
                      </div>
                    </>
                  )}

                {translate.data &&
                  translate.data.article_id === selectedArticle.id && (
                    <>
                      <Separator />
                      <div>
                        <h4 className="mb-1 text-sm font-semibold">
                          Translation ({translate.data.target_language})
                        </h4>
                        <p className="text-sm text-muted-foreground">
                          {translate.data.translated_content}
                        </p>
                      </div>
                    </>
                  )}
              </div>
            </ScrollArea>

            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => summarize.mutate(selectedArticle.id)}
                disabled={summarize.isPending}
              >
                {summarize.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Sparkles className="size-4" />
                )}
                Summarize
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  translate.mutate({
                    articleId: selectedArticle.id,
                    targetLanguage: 'en',
                  })
                }
                disabled={translate.isPending}
              >
                {translate.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Languages className="size-4" />
                )}
                Translate to English
              </Button>
              {selectedArticle.url && (
                <Button variant="outline" size="sm" asChild>
                  <a
                    href={selectedArticle.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <ExternalLink className="size-4" />
                    Open Source
                  </a>
                </Button>
              )}
            </div>
          </DialogContent>
        )}
      </Dialog>
    </div>
  );
}
