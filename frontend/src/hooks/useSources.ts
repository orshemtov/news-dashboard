import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { SourceCreate, SourceUpdate, SourceTestRequest } from '@/types';
import {
  getSources,
  createSource,
  updateSource,
  deleteSource,
  getSourcePresets,
  testSource,
} from '@/api/client';

export function useSources() {
  return useQuery({
    queryKey: ['sources'],
    queryFn: getSources,
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
