import { useLocation } from 'react-router-dom';
import { MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';

const pageTitles: Record<string, string> = {
  '/feed': 'News Feed',
  '/search': 'Search',
  '/sources': 'Sources',
  '/stats': 'Dashboard',
  '/chat': 'Chat',
};

interface HeaderProps {
  onOpenChat: () => void;
}

export function Header({ onOpenChat }: HeaderProps) {
  const location = useLocation();
  const title = pageTitles[location.pathname] ?? 'News Dashboard';

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b bg-background/95 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <h1 className="text-lg font-semibold">{title}</h1>
      <Button variant="outline" size="sm" onClick={onOpenChat}>
        <MessageSquare className="size-4" />
        Chat
      </Button>
    </header>
  );
}
