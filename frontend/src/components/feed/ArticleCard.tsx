import { useState, useRef } from 'react';
import type { Article } from '@/types';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { isRtl, getDisplayTitle, getDisplayContent } from '@/lib/text';
import { thumbnailUrl, mediaUrl, formatDuration } from '@/lib/media';
import { ExternalLink, Video, Play, Image } from 'lucide-react';

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
  onClick: () => void;
  isNew?: boolean;
  onAnimationEnd?: () => void;
}

export function ArticleCard({ article, onClick, isNew, onAnimationEnd }: ArticleCardProps) {
  const title = getDisplayTitle(article.title, article.content);
  const body = getDisplayContent(article.content, 280, title);
  const rtl = isRtl(article.content, article.language);

  const media = article.media_attachments ?? [];
  const firstPhoto = media.find((m) => m.type === 'photo');
  const firstVideo = media.find((m) => m.type === 'video');
  const thumb = firstPhoto ?? firstVideo;
  const thumbSrc = thumb ? thumbnailUrl(thumb) : '';
  const photoCount = media.filter((m) => m.type === 'photo').length;
  const videoCount = media.filter((m) => m.type === 'video').length;

  // Video-only articles get inline playback
  const isVideoOnly = !firstPhoto && !!firstVideo;
  const [playing, setPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleVideoPlay = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPlaying(true);
  };

  return (
    <article
      className={cn(
        'group cursor-pointer rounded-xl border border-border/30 bg-card p-4 transition-all',
        'hover:border-primary/20 hover:bg-accent/40',
        isNew && 'animate-article-enter',
      )}
      onClick={onClick}
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

          {/* Spacer + external link */}
          <div className="flex-1" />
          {article.url && (
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="shrink-0 opacity-0 transition-opacity group-hover:opacity-60 hover:!opacity-100"
            >
              <ExternalLink className="size-3.5" />
            </a>
          )}
        </div>

        {/* Title */}
        <h3
          className="mt-1 text-[15px] font-normal leading-relaxed text-card-foreground line-clamp-3"
          dir={rtl ? 'rtl' : 'ltr'}
        >
          {title}
        </h3>

        {/* Body preview */}
        {body && (
          <p
            className="mt-0.5 text-[15px] leading-relaxed text-muted-foreground line-clamp-3"
            dir={rtl ? 'rtl' : 'ltr'}
          >
            {body}
          </p>
        )}

        {/* Media */}
        {thumbSrc && !isVideoOnly && (
          <div className="relative mt-3 overflow-hidden rounded-xl border border-border/30">
            <div className="aspect-video w-full bg-muted">
              <img
                src={thumbSrc}
                alt=""
                className="h-full w-full object-cover"
                loading="lazy"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
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

        {/* Video — inline player */}
        {isVideoOnly && (
          <div
            className="relative mt-3 overflow-hidden rounded-xl border border-border/30"
            onClick={handleVideoPlay}
          >
            {playing ? (
              <video
                ref={videoRef}
                src={mediaUrl(firstVideo.url)}
                controls
                autoPlay
                muted
                className="w-full"
                style={{ maxHeight: '400px' }}
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <div className="aspect-video w-full bg-muted">
                {thumbSrc ? (
                  <img
                    src={thumbSrc}
                    alt=""
                    className="h-full w-full object-cover"
                    loading="lazy"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-muted">
                    <Video className="size-8 text-muted-foreground/40" />
                  </div>
                )}
                {/* Play button overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="rounded-full bg-black/60 p-3 transition-transform group-hover:scale-110">
                    <Play className="size-6 text-white" fill="white" />
                  </div>
                </div>
                {/* Duration badge */}
                {firstVideo.duration != null && firstVideo.duration > 0 && (
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
