import { useQuery } from '@tanstack/react-query';
import { getStats } from '@/api/client';

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    refetchInterval: 30000,
  });
}
