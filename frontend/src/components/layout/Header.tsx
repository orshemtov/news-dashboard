import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Newspaper, Radio, Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';


export function Header() {
  const location = useLocation();
  const [dark, setDark] = useState(() =>
    document.documentElement.classList.contains('dark'),
  );

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);

  return (
    <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur-lg">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
        {/* Left: branding */}
        <Link to="/" className="flex items-center gap-2">
          <Newspaper className="size-5 text-primary" />
          <span className="text-lg font-semibold tracking-tight">
            News Feed
          </span>
        </Link>

        {/* Right: nav + toggle */}
        <div className="flex items-center gap-1">
          <Button
            variant={location.pathname === '/' ? 'secondary' : 'ghost'}
            size="sm"
            asChild
          >
            <Link to="/">
              <Newspaper className="size-4" />
              <span className="hidden sm:inline">Feed</span>
            </Link>
          </Button>
          <Button
            variant={location.pathname === '/sources' ? 'secondary' : 'ghost'}
            size="sm"
            asChild
          >
            <Link to="/sources">
              <Radio className="size-4" />
              <span className="hidden sm:inline">Sources</span>
            </Link>
          </Button>

          <div className="mx-1 h-5 w-px bg-border" />

          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={() => setDark((d) => !d)}
            aria-label="Toggle dark mode"
          >
            {dark ? (
              <Sun className="size-4" />
            ) : (
              <Moon className="size-4" />
            )}
          </Button>
        </div>
      </div>
    </header>
  );
}
