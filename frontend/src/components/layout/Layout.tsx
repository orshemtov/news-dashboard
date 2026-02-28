import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { ChatPanel } from '@/components/chat/ChatPanel';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';

export function Layout() {
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <div className="flex flex-1 flex-col pl-64">
        <Header onOpenChat={() => setChatOpen(true)} />

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>

      <Sheet open={chatOpen} onOpenChange={setChatOpen}>
        <SheetContent side="right" className="w-full sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Chat with AI</SheetTitle>
          </SheetHeader>
          <ChatPanel />
        </SheetContent>
      </Sheet>
    </div>
  );
}
