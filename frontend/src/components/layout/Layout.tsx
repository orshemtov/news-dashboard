import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { BottomNav } from './BottomNav';

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col overflow-x-hidden pb-16 md:pb-0">
      <Header />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 overflow-x-hidden">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}
