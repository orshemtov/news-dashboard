import { useStats } from '@/hooks/useStats';
import { Activity, CalendarDays, Radio } from 'lucide-react';

export function StatsBar() {
  const { data: stats } = useStats();

  if (!stats) return null;

  const items = [
    {
      label: 'Articles',
      value: stats.total_articles.toLocaleString(),
      icon: Activity,
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
    <div className="flex items-center gap-4 text-sm">
      {items.map((item, i) => (
        <div key={item.label} className="flex items-center gap-2">
          {i > 0 && <div className="h-3 w-px bg-border/50" />}
          <div className="flex items-center gap-1.5">
            <item.icon className="size-3 text-primary/60" />
            <span className="text-muted-foreground/70 text-xs">{item.label}</span>
            <span className="text-xs font-medium">{item.value}</span>
          </div>
        </div>
      ))}
      {stats.latest_ingestion && (
        <>
          <div className="h-3 w-px bg-border/50" />
          <span className="text-[11px] text-muted-foreground/50">
            {new Date(stats.latest_ingestion).toLocaleTimeString()}
          </span>
        </>
      )}
    </div>
  );
}
