import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, Radio, Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';


export function Header() {
  const location = useLocation();
  const [dark, setDark] = useState(() =>
    document.documentElement.classList.contains('dark'),
  );

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);

  const navItem = (path: string, icon: React.ReactNode, label: string) => {
    const active = location.pathname === path;
    return (
      <Link
        to={path}
        className={cn(
          'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
          active
            ? 'text-primary'
            : 'text-muted-foreground hover:text-foreground',
        )}
      >
        {icon}
        <span className="hidden sm:inline">{label}</span>
      </Link>
    );
  };

  return (
    <header className="sticky top-0 z-30 border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-12 max-w-6xl items-center justify-between px-4 sm:px-6">
        {/* Left: branding */}
        <Link to="/" className="flex items-center gap-2 group">
          <Activity className="size-4 text-primary transition-transform group-hover:scale-110" />
          <span className="text-[15px] font-semibold tracking-tight">
            Pulse
          </span>
        </Link>

        {/* Right: nav + toggle */}
        <div className="flex items-center gap-0.5">
          {navItem('/', <Activity className="size-3.5" />, 'Feed')}
          {navItem('/sources', <Radio className="size-3.5" />, 'Sources')}

          <div className="mx-2 h-4 w-px bg-border/50" />

          <Button
            variant="ghost"
            size="icon"
            className="size-7 text-muted-foreground hover:text-foreground"
            onClick={() => setDark((d) => !d)}
            aria-label="Toggle dark mode"
          >
            {dark ? (
              <Sun className="size-3.5" />
            ) : (
              <Moon className="size-3.5" />
            )}
          </Button>
        </div>
      </div>
    </header>
  );
}
