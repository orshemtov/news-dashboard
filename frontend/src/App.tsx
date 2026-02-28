import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import Feed from '@/pages/Feed';
import Search from '@/pages/Search';
import Sources from '@/pages/Sources';
import Stats from '@/pages/Stats';
import Chat from '@/pages/Chat';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/feed" element={<Feed />} />
            <Route path="/search" element={<Search />} />
            <Route path="/sources" element={<Sources />} />
            <Route path="/stats" element={<Stats />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/" element={<Navigate to="/feed" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
