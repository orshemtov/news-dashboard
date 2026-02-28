import { useStats } from '@/hooks/useStats';
import { Newspaper, CalendarDays, Radio } from 'lucide-react';

export function StatsBar() {
  const { data: stats } = useStats();

  if (!stats) return null;

  const items = [
    {
      label: 'Articles',
      value: stats.total_articles.toLocaleString(),
      icon: Newspaper,
    },
    {
      label: 'Today',
      value: stats.articles_today.toLocaleString(),
      icon: CalendarDays,
    },
    {
      label: 'Sources',
      value: `${stats.active_sources}/${stats.total_sources}`,
      icon: Radio,
    },
  ];

  return (
    <div className="flex items-center gap-4 rounded-lg border border-border/50 bg-card px-4 py-2.5">
      {items.map((item, i) => (
        <div key={item.label} className="flex items-center gap-3">
          {i > 0 && <div className="h-4 w-px bg-border" />}
          <div className="flex items-center gap-2">
            <item.icon className="size-3.5 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{item.label}</span>
            <span className="text-sm font-semibold">{item.value}</span>
          </div>
        </div>
      ))}
      {stats.latest_ingestion && (
        <>
          <div className="h-4 w-px bg-border" />
          <span className="text-xs text-muted-foreground">
            Last ingest:{' '}
            {new Date(stats.latest_ingestion).toLocaleTimeString()}
          </span>
        </>
      )}
    </div>
  );
}
