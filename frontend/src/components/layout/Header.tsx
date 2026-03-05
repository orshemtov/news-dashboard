import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, Radio, Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useHealth } from '@/hooks/useHealth';


export function Header() {
  const location = useLocation();
  const { data: health, isError: healthError } = useHealth();
  const [dark, setDark] = useState(() =>
    document.documentElement.classList.contains('dark'),
  );

  const buildTime = new Date(__APP_BUILD_TIME__);
  const buildLabel = Number.isNaN(buildTime.getTime())
    ? __APP_VERSION__
    : `v${__APP_VERSION__} ${buildTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;

  const healthState = healthError
    ? 'offline'
    : health?.status === 'ok'
      ? 'online'
      : 'degraded';
  const healthClass =
    healthState === 'online'
      ? 'bg-emerald-500'
      : healthState === 'degraded'
        ? 'bg-amber-500'
        : 'bg-rose-500';
  const healthText =
    healthState === 'online'
      ? `Backend online${health?.telegram ? ` • Telegram ${health.telegram}` : ''}`
      : healthState === 'degraded'
        ? `Backend degraded${health?.telegram ? ` • Telegram ${health.telegram}` : ''}`
        : 'Backend offline';

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('pulse-theme', dark ? 'dark' : 'light');
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
    <header className="sticky top-0 z-40 border-b border-border/30 bg-background/60 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        {/* Left: branding */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="flex size-7 items-center justify-center rounded-lg bg-primary/10 transition-colors group-hover:bg-primary/20">
            <Activity className="size-4 text-primary transition-transform group-hover:scale-110" />
          </div>
          <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
            Pulse
          </span>
          <span className="hidden rounded-full border border-border/50 bg-muted/40 px-2 py-0.5 text-[10px] font-medium text-muted-foreground sm:inline">
            {buildLabel}
          </span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-1">
          {navItem('/', <Activity className="size-3.5" />, 'Feed')}
          {navItem('/sources', <Radio className="size-3.5" />, 'Sources')}

          <div className="flex items-center gap-1.5 rounded-full border border-border/50 bg-muted/30 px-2 py-1 text-[11px] text-muted-foreground" title={healthText}>
            <span className={cn('inline-block size-2 rounded-full', healthClass)} />
            <span className="uppercase tracking-wide">{healthState}</span>
          </div>

          <div className="mx-2 h-4 w-px bg-border/50" />
          
          <Button
            variant="ghost"
            size="icon"
            className="size-8 text-muted-foreground hover:text-foreground hover:bg-accent"
            onClick={() => setDark((d) => !d)}
            title="Toggle theme"
          >
            {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
        </div>

        {/* Mobile Theme Toggle */}
        <div className="flex md:hidden items-center gap-2">
          <span className="rounded-full border border-border/50 bg-muted/30 px-1.5 py-0.5 text-[10px] text-muted-foreground" title={healthText}>
            <span className={cn('mr-1 inline-block size-1.5 rounded-full align-middle', healthClass)} />
            {healthState}
          </span>
          <Button
            variant="ghost"
            size="icon"
            className="size-9 text-muted-foreground hover:text-foreground"
            onClick={() => setDark((d) => !d)}
          >
            {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
        </div>
      </div>
    </header>
  );
}
