import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { ChatMessageRequest } from '@/types';
import {
  getConversations,
  getConversation,
  sendChatMessage,
  deleteConversation,
} from '@/api/client';

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: getConversations,
  });
}

export function useConversation(id: string) {
  return useQuery({
    queryKey: ['conversations', id],
    queryFn: () => getConversation(id),
    enabled: !!id,
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ChatMessageRequest) => sendChatMessage(data),
    onSuccess: (_data, variables) => {
      if (variables.conversation_id) {
        queryClient.invalidateQueries({
          queryKey: ['conversations', variables.conversation_id],
        });
      }
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}
