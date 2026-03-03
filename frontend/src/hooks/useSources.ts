import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { SourceCreate, SourceUpdate, SourceTestRequest } from '@/types';
import {
  getSources,
  createSource,
  updateSource,
  deleteSource,
  getSourcePresets,
  testSource,
  ingestSource,
  searchTelegramChannels,
  getChannelSuggestions,
} from '@/api/client';

export function useSources() {
  return useQuery({
    queryKey: ['sources'],
    queryFn: getSources,
    staleTime: 30_000, // treat as fresh for 30s — sources don't change rapidly
  });
}

export function useSourcePresets() {
  return useQuery({
    queryKey: ['sourcePresets'],
    queryFn: getSourcePresets,
  });
}

export function useCreateSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SourceCreate) => createSource(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
  });
}

export function useUpdateSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SourceUpdate }) =>
      updateSource(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
  });
}

export function useDeleteSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
  });
}

export function useTestSource() {
  return useMutation({
    mutationFn: (data: SourceTestRequest) => testSource(data),
  });
}

export function useIngestSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ingestSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
}

export function useSearchTelegramChannels(query: string) {
  return useQuery({
    queryKey: ['telegramSearch', query],
    queryFn: () => searchTelegramChannels(query),
    enabled: query.trim().length >= 2,
    staleTime: 30_000,
  });
}

export function useChannelSuggestions() {
  return useQuery({
    queryKey: ['channelSuggestions'],
    queryFn: () => getChannelSuggestions(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
