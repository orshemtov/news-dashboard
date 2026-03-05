import { useQuery } from '@tanstack/react-query';
import { TrendingUp, Clock, FileText } from 'lucide-react';
import api from '@/api/client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { timeAgo } from './ArticleCard';

interface Theme {
  id: string;
  theme: string;
  article_count: number;
  source_count: number;
  last_update: string;
  lead_id: string;
}

interface TrendingThemesProps {
  onThemeClick?: (clusterId: string) => void;
  sticky?: boolean;
}

export function TrendingThemes({ onThemeClick, sticky = true }: TrendingThemesProps) {
  const { data: themes, isLoading, isError } = useQuery<Theme[]>({
    queryKey: ['trending-themes'],
    queryFn: async () => {
      const { data } = await api.get('/stats/trending?window_minutes=180&limit=10&min_sources=2');
      return data;
    },
    refetchInterval: 60 * 1000, // Refresh every minute
  });

  if (isLoading) {
    return (
      <Card className="border-border/30 bg-card/50">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <TrendingUp className="size-4 text-orange-500" />
            Trending Now
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-3 w-2/3" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={sticky ? 'sticky top-20 max-h-[calc(100vh-6rem)] overflow-y-auto border-border/40 bg-card/80' : 'border-border/40 bg-card/80'}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold">
          <div className="relative flex size-4 items-center justify-center">
            <div className="absolute inline-flex h-full w-full animate-ping rounded-full bg-orange-400 opacity-20"></div>
            <TrendingUp className="relative size-4 text-orange-500" />
          </div>
          Trending Now
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-0 px-0 pb-2">
        {isError && (
          <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive">
            Trending API unavailable
          </div>
        )}
        {!isError && (!themes || themes.length === 0) && (
          <div className="rounded-md border border-border/40 bg-muted/20 px-3 py-2 text-xs text-muted-foreground">
            No multi-source themes in the last hour yet.
          </div>
        )}
        {(themes ?? []).map((theme) => {
          return (
            <button
              key={theme.id}
              onClick={() => onThemeClick?.(theme.id)}
              className="group flex w-full flex-col gap-1.5 border-y border-transparent px-4 py-3 text-left transition-colors hover:border-border/50 hover:bg-accent/30"
            >
              <h4 className="text-[13px] font-medium leading-relaxed text-card-foreground line-clamp-6" dir="auto">
                {theme.theme}
              </h4>
              
              <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1 font-medium text-orange-600/80">
                  <FileText className="size-3" />
                  {theme.source_count} sources
                </span>
                
                <span className="flex items-center gap-1">
                  <Clock className="size-3" />
                  {timeAgo(theme.last_update)}
                </span>
              </div>
            </button>
          );
        })}
      </CardContent>
    </Card>
  );
}
