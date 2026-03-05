import { useQuery } from '@tanstack/react-query';
import { getHealth } from '@/api/client';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 15000,
    retry: 0,
  });
}
