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
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-1">
          {navItem('/', <Activity className="size-3.5" />, 'Feed')}
          {navItem('/sources', <Radio className="size-3.5" />, 'Sources')}
          
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
        <div className="flex md:hidden items-center">
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
