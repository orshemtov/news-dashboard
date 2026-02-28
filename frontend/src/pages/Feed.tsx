import { useState } from 'react';
import { useArticles } from '@/hooks/useArticles';
import { useSummarize, useTranslate } from '@/hooks/useAI';
import type { Article } from '@/types';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Sparkles,
  Languages,
  Loader2,
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

export default function Feed() {
  const [page, setPage] = useState(1);
  const [sourceType, setSourceType] = useState<string>('');
  const [language, setLanguage] = useState<string>('');
  const [hideDuplicates, setHideDuplicates] = useState(true);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);

  const { data, isLoading, isError } = useArticles({
    page,
    page_size: 20,
    source_type: sourceType || undefined,
    language: language || undefined,
    is_duplicate: hideDuplicates ? false : undefined,
  });

  const summarize = useSummarize();
  const translate = useTranslate();

  const articles = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 20);

  return (
    <div className="space-y-6">
      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={sourceType}
          onChange={(e) => {
            setSourceType(e.target.value);
            setPage(1);
          }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All Sources</option>
          <option value="rss">RSS</option>
          <option value="telegram">Telegram</option>
        </select>

        <Input
          placeholder="Language (e.g. en, he)"
          value={language}
          onChange={(e) => {
            setLanguage(e.target.value);
            setPage(1);
          }}
          className="w-40"
        />

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={hideDuplicates}
            onChange={(e) => {
              setHideDuplicates(e.target.checked);
              setPage(1);
            }}
            className="rounded border-input"
          />
          Hide duplicates
        </label>

        <span className="ml-auto text-sm text-muted-foreground">
          {total} articles
        </span>
      </div>

      {/* Loading / Error */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      )}
      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load articles. The backend may be unavailable.
        </div>
      )}

      {/* Article Cards */}
      <div className="grid gap-3">
        {articles.map((article) => (
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
                {article.is_duplicate && (
                  <Badge variant="destructive">Duplicate</Badge>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
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

                {selectedArticle.summary && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="mb-1 text-sm font-semibold">Summary</h4>
                      <p className="text-sm text-muted-foreground">
                        {selectedArticle.summary}
                      </p>
                    </div>
                  </>
                )}

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
