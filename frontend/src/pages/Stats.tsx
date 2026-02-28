import { useStats } from '@/hooks/useStats';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Newspaper,
  CalendarDays,
  Radio,
  Loader2,
} from 'lucide-react';

export default function Stats() {
  const { data: stats, isLoading, isError } = useStats();

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError || !stats) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
        Failed to load stats. The backend may be unavailable.
      </div>
    );
  }

  // Find max for bar scaling
  const maxBySource = Math.max(
    1,
    ...Object.values(stats.articles_by_source)
  );
  const maxByHour = Math.max(
    1,
    ...stats.articles_by_hour.map((h) => h.count)
  );
  const maxByLang = Math.max(
    1,
    ...Object.values(stats.languages)
  );

  return (
    <div className="space-y-6">
      {/* Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Total Articles
            </CardTitle>
            <Newspaper className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.total_articles.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Articles Today
            </CardTitle>
            <CalendarDays className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.articles_today.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Active Sources
            </CardTitle>
            <Radio className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.active_sources}{' '}
              <span className="text-sm font-normal text-muted-foreground">
                / {stats.total_sources}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Articles by Source */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Articles by Source</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(stats.articles_by_source).length === 0 && (
              <p className="text-sm text-muted-foreground">No data yet</p>
            )}
            {Object.entries(stats.articles_by_source)
              .sort(([, a], [, b]) => b - a)
              .map(([name, count]) => (
                <div key={name} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="truncate">{name}</span>
                    <span className="text-muted-foreground">{count}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-secondary">
                    <div
                      className="h-full rounded-full bg-primary transition-all"
                      style={{
                        width: `${(count / maxBySource) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
          </CardContent>
        </Card>

        {/* Articles by Hour */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Articles by Hour (last 24h)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-48 items-end gap-1">
              {stats.articles_by_hour.map((h) => (
                <div
                  key={h.hour}
                  className="group relative flex flex-1 flex-col items-center"
                >
                  <div
                    className="w-full rounded-t bg-primary/80 transition-colors group-hover:bg-primary"
                    style={{
                      height: `${Math.max(2, (h.count / maxByHour) * 100)}%`,
                    }}
                  />
                  <span className="mt-1 text-[10px] text-muted-foreground">
                    {h.hour.split('T')[1]?.slice(0, 2) ??
                      new Date(h.hour).getHours()}
                  </span>
                  {/* Tooltip on hover */}
                  <span className="pointer-events-none absolute -top-6 rounded bg-foreground px-1.5 py-0.5 text-[10px] text-background opacity-0 transition-opacity group-hover:opacity-100">
                    {h.count}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Languages */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Languages</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(stats.languages).length === 0 && (
              <p className="text-sm text-muted-foreground">No data yet</p>
            )}
            {Object.entries(stats.languages)
              .sort(([, a], [, b]) => b - a)
              .map(([lang, count]) => (
                <div key={lang} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <Badge variant="outline">{lang || 'Unknown'}</Badge>
                    <span className="text-muted-foreground">{count}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-secondary">
                    <div
                      className="h-full rounded-full bg-chart-2 transition-all"
                      style={{
                        width: `${(count / maxByLang) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
          </CardContent>
        </Card>

        {/* Last Ingestion */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">System Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Latest Ingestion</span>
              <span>
                {stats.latest_ingestion
                  ? new Date(stats.latest_ingestion).toLocaleString()
                  : 'N/A'}
              </span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Sources</span>
              <span>{stats.total_sources}</span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-muted-foreground">Active Sources</span>
              <span>{stats.active_sources}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
