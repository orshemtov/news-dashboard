import { Link, useLocation } from 'react-router-dom';
import { Newspaper, Settings2 } from 'lucide-react';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { label: 'Feed', icon: Newspaper, path: '/' },
  { label: 'Sources', icon: Settings2, path: '/sources' },
];

export function BottomNav() {
  const location = useLocation();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-border/50 bg-background/80 pb-safe-area-inset-bottom backdrop-blur-lg md:hidden">
      <div className="flex h-16 items-center justify-around px-4">
        {NAV_ITEMS.map((item) => {
          const active = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex flex-col items-center justify-center gap-1 transition-colors',
                active ? 'text-primary' : 'text-muted-foreground'
              )}
            >
              <item.icon className={cn('size-6 transition-transform', active && 'scale-110')} />
              <span className="text-[10px] font-medium uppercase tracking-wider">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
