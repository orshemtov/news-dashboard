import { NavLink } from 'react-router-dom';
import {
  Newspaper,
  Search,
  Radio,
  BarChart3,
  MessageSquare,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Separator } from '@/components/ui/separator';

const navItems = [
  { to: '/feed', label: 'Feed', icon: Newspaper },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/sources', label: 'Sources', icon: Radio },
  { to: '/stats', label: 'Stats', icon: BarChart3 },
  { to: '/chat', label: 'Chat', icon: MessageSquare },
];

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-zinc-900 text-white">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 px-5">
        <Newspaper className="size-5 text-blue-400" />
        <span className="text-lg font-semibold tracking-tight">
          News Dashboard
        </span>
      </div>

      <Separator className="bg-zinc-700/50" />

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-zinc-700/60 text-white'
                  : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
              )
            }
          >
            <Icon className="size-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-zinc-700/50 px-5 py-3">
        <p className="text-xs text-zinc-500">News Aggregator v1.0</p>
      </div>
    </aside>
  );
}
