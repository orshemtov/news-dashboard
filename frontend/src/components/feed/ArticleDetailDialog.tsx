import { useState, useEffect, useCallback } from 'react';
import type { Article, MediaAttachment } from '@/types';
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
import { ExternalLink, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { isRtl, cleanContent, getDisplayTitle } from '@/lib/text';
import { mediaUrl, formatFileSize, formatDuration } from '@/lib/media';
import { cn } from '@/lib/utils';

interface ArticleDetailDialogProps {
  article: Article | null;
  onClose: () => void;
}

export function ArticleDetailDialog({
  article,
  onClose,
}: ArticleDetailDialogProps) {
  const rtl = article ? isRtl(article.content, article.language) : false;
  const media = article?.media_attachments ?? [];

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
              {/* Media gallery */}
              {media.length > 0 && (
                <MediaGallery attachments={media} />
              )}

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

// ---------------------------------------------------------------------------
// Media Gallery Component
// ---------------------------------------------------------------------------

function MediaGallery({ attachments }: { attachments: MediaAttachment[] }) {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  return (
    <>
      {/* Thumbnail grid */}
      <div
        className={cn(
          'grid gap-2',
          attachments.length === 1 && 'grid-cols-1',
          attachments.length === 2 && 'grid-cols-2',
          attachments.length >= 3 && 'grid-cols-2 sm:grid-cols-3',
        )}
      >
        {attachments.map((att, i) => (
          <button
            key={att.url}
            type="button"
            className="group/media relative aspect-video overflow-hidden rounded-md bg-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            onClick={() => setLightboxIndex(i)}
          >
            {att.type === 'photo' ? (
              <img
                src={mediaUrl(att.url)}
                alt=""
                className="h-full w-full object-contain transition-transform group-hover/media:scale-105"
                loading="lazy"
              />
            ) : (
              <>
                {att.thumbnail_url ? (
                  <img
                    src={mediaUrl(att.thumbnail_url)}
                    alt=""
                    className="h-full w-full object-contain"
                    loading="lazy"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-muted">
                    <span className="text-2xl text-muted-foreground">
                      &#9654;
                    </span>
                  </div>
                )}
                {/* Play icon overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="rounded-full bg-black/60 p-2">
                    <span className="text-lg text-white">&#9654;</span>
                  </div>
                </div>
                {/* Duration badge */}
                {att.duration != null && att.duration > 0 && (
                  <span className="absolute bottom-1 right-1 rounded bg-black/70 px-1.5 py-0.5 text-[11px] font-medium text-white">
                    {formatDuration(att.duration)}
                  </span>
                )}
              </>
            )}
          </button>
        ))}
      </div>

      {/* Lightbox */}
      {lightboxIndex !== null && (
        <MediaLightbox
          attachments={attachments}
          index={lightboxIndex}
          onIndexChange={setLightboxIndex}
          onClose={() => setLightboxIndex(null)}
        />
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Media Lightbox Component
// ---------------------------------------------------------------------------

function MediaLightbox({
  attachments,
  index,
  onIndexChange,
  onClose,
}: {
  attachments: MediaAttachment[];
  index: number;
  onIndexChange: (i: number) => void;
  onClose: () => void;
}) {
  const att = attachments[index];
  const hasPrev = index > 0;
  const hasNext = index < attachments.length - 1;

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      else if (e.key === 'ArrowLeft' && hasPrev) onIndexChange(index - 1);
      else if (e.key === 'ArrowRight' && hasNext) onIndexChange(index + 1);
    },
    [onClose, onIndexChange, index, hasPrev, hasNext],
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/90"
      onClick={onClose}
    >
      {/* Close button */}
      <button
        type="button"
        className="absolute top-4 right-4 z-10 rounded-full bg-white/10 p-2 text-white hover:bg-white/20"
        onClick={onClose}
      >
        <X className="size-5" />
      </button>

      {/* Previous */}
      {hasPrev && (
        <button
          type="button"
          className="absolute left-4 z-10 rounded-full bg-white/10 p-2 text-white hover:bg-white/20"
          onClick={(e) => {
            e.stopPropagation();
            onIndexChange(index - 1);
          }}
        >
          <ChevronLeft className="size-6" />
        </button>
      )}

      {/* Media content */}
      <div
        className="max-h-[85vh] max-w-[90vw]"
        onClick={(e) => e.stopPropagation()}
      >
        {att.type === 'photo' ? (
          <img
            src={mediaUrl(att.url)}
            alt=""
            className="max-h-[85vh] max-w-[90vw] rounded object-contain"
          />
        ) : (
          <video
            src={mediaUrl(att.url)}
            controls
            autoPlay
            muted
            className="max-h-[85vh] max-w-[90vw] rounded"
          >
            Your browser does not support the video tag.
          </video>
        )}
      </div>

      {/* Next */}
      {hasNext && (
        <button
          type="button"
          className="absolute right-4 z-10 rounded-full bg-white/10 p-2 text-white hover:bg-white/20"
          onClick={(e) => {
            e.stopPropagation();
            onIndexChange(index + 1);
          }}
        >
          <ChevronRight className="size-6" />
        </button>
      )}

      {/* Counter */}
      {attachments.length > 1 && (
        <span className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-black/60 px-3 py-1 text-sm text-white">
          {index + 1} / {attachments.length}
        </span>
      )}

      {/* File info */}
      {att.file_size != null && (
        <span className="absolute bottom-4 right-4 text-xs text-white/60">
          {formatFileSize(att.file_size)}
        </span>
      )}
    </div>
  );
}
