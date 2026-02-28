import type { Article } from '@/types';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { isRtl, getDisplayTitle, getDisplayContent } from '@/lib/text';
import { ExternalLink } from 'lucide-react';

export function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

interface ArticleCardProps {
  article: Article;
  onClick: () => void;
}

export function ArticleCard({ article, onClick }: ArticleCardProps) {
  const title = getDisplayTitle(article.title, article.content);
  const body = getDisplayContent(article.content, 200, title);
  const rtl = isRtl(article.content, article.language);

  return (
    <article
      className={cn(
        'group cursor-pointer rounded-lg border border-border/40 bg-card p-4 transition-all',
        'hover:border-border hover:bg-accent/30',
      )}
      dir={rtl ? 'rtl' : 'ltr'}
      onClick={onClick}
    >
      {/* Title */}
      <h3 className="line-clamp-3 text-[15px] font-medium leading-relaxed text-card-foreground">
        {title}
      </h3>

      {/* Body preview */}
      {body && (
        <p className="mt-1.5 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
          {body}
        </p>
      )}

      {/* Footer: metadata row — dir inherited from article, flex follows naturally */}
      <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
        <Badge variant="secondary" className="text-[11px] font-normal">
          {article.source_name}
        </Badge>

        <span className="opacity-60">{timeAgo(article.published_at)}</span>

        {article.language && (
          <span className="uppercase opacity-50">{article.language}</span>
        )}

        {article.is_duplicate && (
          <Badge variant="destructive" className="text-[11px]">
            dup
          </Badge>
        )}

        {/* Spacer pushes link icon to the opposite end */}
        <div className="flex-1" />

        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="opacity-0 transition-opacity group-hover:opacity-60 hover:!opacity-100"
          >
            <ExternalLink className="size-3.5" />
          </a>
        )}
      </div>
    </article>
  );
}
