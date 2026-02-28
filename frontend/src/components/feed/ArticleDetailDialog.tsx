import type { Article } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { ExternalLink } from 'lucide-react';
import { isRtl, cleanContent, getDisplayTitle } from '@/lib/text';

interface ArticleDetailDialogProps {
  article: Article | null;
  onClose: () => void;
}

export function ArticleDetailDialog({
  article,
  onClose,
}: ArticleDetailDialogProps) {
  const rtl = article ? isRtl(article.content, article.language) : false;

  return (
    <Dialog open={!!article} onOpenChange={(open) => !open && onClose()}>
      {article && (
        <DialogContent className="max-h-[85vh] sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle dir={rtl ? 'rtl' : 'ltr'}>
              {getDisplayTitle(article.title, article.content)}
            </DialogTitle>
            <DialogDescription asChild>
              <span className="flex items-center gap-2">
                <Badge variant="secondary">{article.source_name}</Badge>
                <span className="text-xs">
                  {new Date(article.published_at).toLocaleString()}
                </span>
              </span>
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="max-h-[50vh]">
            <div className="space-y-4 pr-4" dir={rtl ? 'rtl' : 'ltr'}>
              <p className="whitespace-pre-wrap text-sm leading-relaxed">
                {cleanContent(article.content)}
              </p>

              {article.summary && (
                <>
                  <Separator />
                  <div>
                    <h4 className="mb-1 text-sm font-semibold">Summary</h4>
                    <p className="text-sm text-muted-foreground">
                      {article.summary}
                    </p>
                  </div>
                </>
              )}

            </div>
          </ScrollArea>

          <div className="flex flex-wrap gap-2">
            {article.url && (
              <Button variant="outline" size="sm" asChild>
                <a
                  href={article.url}
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
  );
}
