import type { Article } from '@/types';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { isRtl, getDisplayTitle, getDisplayContent } from '@/lib/text';
import { mediaUrl, thumbnailUrl, formatDuration } from '@/lib/media';
import { TrendingUp, ExternalLink, Video, Image, EyeOff, Eye } from 'lucide-react';

export function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

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

interface ArticleCardProps {
  article: Article;
  onHide?: (e: React.MouseEvent) => void;
  isNew?: boolean;
  isHiddenOnlyMode?: boolean;
  isTrending?: boolean;
  trendCount?: number;
  onAnimationEnd?: () => void;
}

export function ArticleCard({ article, onHide, isNew, isHiddenOnlyMode, isTrending, trendCount, onAnimationEnd }: ArticleCardProps) {
  const title = getDisplayTitle(article.title, article.content);
  const body = getDisplayContent(article.content, undefined, title);
  const rtl = isRtl(article.content, article.language);

  const media = article.media_attachments ?? [];
  const firstPhoto = media.find((m) => m.type === 'photo');
  const firstVideo = media.find((m) => m.type === 'video');
  const thumb = firstPhoto ?? firstVideo;
  const thumbSrc = thumb ? thumbnailUrl(thumb) : '';
  const photoCount = media.filter((m) => m.type === 'photo').length;
  const videoCount = media.filter((m) => m.type === 'video').length;

  const handleVideoPlay = (event: React.SyntheticEvent<HTMLVideoElement>) => {
    const current = event.currentTarget;
    const videos = document.querySelectorAll<HTMLVideoElement>('video[data-feed-video="true"]');
    videos.forEach((video) => {
      if (video !== current) {
        video.pause();
      }
    });
  };

  return (
    <article
      className={cn(
        'group rounded-xl border border-border/30 bg-card p-4 transition-all',
        'hover:border-primary/20 hover:bg-accent/40',
        isTrending && 'border-orange-500/20 shadow-lg shadow-orange-500/5 ring-1 ring-orange-500/10 bg-gradient-to-br from-card to-orange-500/5',
        isNew && 'animate-article-enter',
      )}
      onAnimationEnd={onAnimationEnd}
    >
      {/* Content */}
      <div className="min-w-0">
        {/* Header: source · time — always LTR */}
        <div className="flex items-center gap-1.5 text-[13px]" dir="ltr">
          <span className={cn('inline-block size-2 shrink-0 rounded-full', sourceColor(article.source_name))} />
          <span className="font-semibold text-card-foreground truncate">
            {article.source_name}
          </span>
          <span className="shrink-0 text-muted-foreground/60">{timeAgo(article.published_at)}</span>

          {article.is_duplicate && (
            <Badge variant="destructive" className="ml-1 text-[10px] px-1.5 py-0">
              dup
            </Badge>
          )}

          {isTrending && (
            <Badge variant="secondary" className="ml-1 bg-orange-500/15 text-orange-600 border-orange-500/20 text-[10px] px-1.5 py-0 hover:bg-orange-500/20">
              <TrendingUp className="mr-1 size-2.5" />
              Trending {trendCount && trendCount > 1 ? `(${trendCount})` : ''}
            </Badge>
          )}

          {/* Spacer + actions */}
          <div className="flex-1" />
          <div className="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
            {onHide && (
              <button
                onClick={onHide}
                className={cn(
                  "shrink-0 transition-colors p-1",
                  isHiddenOnlyMode ? "text-primary hover:text-primary/80" : "text-muted-foreground hover:text-destructive"
                )}
                title={isHiddenOnlyMode ? "Unhide article" : "Hide article"}
              >
                {isHiddenOnlyMode ? <Eye className="size-3.5" /> : <EyeOff className="size-3.5" />}
              </button>
            )}
            {article.url && (
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="shrink-0 text-muted-foreground hover:text-foreground p-1"
              >
                <ExternalLink className="size-3.5" />
              </a>
            )}
          </div>
        </div>

        {/* Title */}
        <h3
          className="mt-1 text-[15px] font-normal leading-relaxed text-card-foreground"
          dir={rtl ? 'rtl' : 'ltr'}
        >
          {title}
        </h3>

        {/* Body preview */}
        {body && (
          <p
            className="mt-0.5 whitespace-pre-wrap text-[15px] leading-relaxed text-muted-foreground"
            dir={rtl ? 'rtl' : 'ltr'}
          >
            {body}
          </p>
        )}

        {/* Media */}
        {thumbSrc && (
          <div className="relative mt-3 overflow-hidden rounded-xl border border-border/30">
            <div className="aspect-video w-full bg-muted">
              {firstVideo ? (
                <video
                  src={mediaUrl(firstVideo.url)}
                  controls
                  preload="metadata"
                  playsInline
                  data-feed-video="true"
                  onPlay={handleVideoPlay}
                  className="h-full w-full object-contain"
                >
                  Your browser does not support the video tag.
                </video>
              ) : (
                <img
                  src={thumbSrc}
                  alt=""
                  className="h-full w-full object-contain"
                  loading="lazy"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              )}
            </div>
            
            {/* Video duration overlay */}
            {firstVideo?.duration != null && firstVideo.duration > 0 && (
              <span className="absolute bottom-2 left-2 rounded bg-black/75 px-1.5 py-0.5 text-[11px] font-medium text-white">
                {formatDuration(firstVideo.duration)}
              </span>
            )}
            {/* Multi-media count badge */}
            {media.length > 1 && (
              <span className="absolute top-2 right-2 rounded-full bg-black/70 px-2 py-0.5 text-[11px] font-medium text-white">
                1/{media.length}
              </span>
            )}
          </div>
        )}

        {/* Inline media badges when no visual media shown */}
        {!thumbSrc && (photoCount > 0 || videoCount > 0) && (
          <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground/60">
            {photoCount > 0 && (
              <span className="flex items-center gap-0.5">
                <Image className="size-3.5" />
                {photoCount > 1 && photoCount}
              </span>
            )}
            {videoCount > 0 && (
              <span className="flex items-center gap-0.5">
                <Video className="size-3.5" />
                {videoCount > 1 && videoCount}
              </span>
            )}
          </div>
        )}
      </div>
    </article>
  );
}
