import { useState } from 'react';
import { Trash2, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  useConversations,
  useConversation,
  useSendMessage,
  useDeleteConversation,
} from '@/hooks/useChat';
import type { ChatMessage } from '@/types';

export default function Chat() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');

  const { data: conversationsData } = useConversations();
  const conversations = conversationsData?.items ?? [];
  const { data: activeConversation } = useConversation(selectedId ?? '');
  const sendMessage = useSendMessage();
  const deleteConversation = useDeleteConversation();

  const displayMessages = selectedId && activeConversation
    ? activeConversation.messages
    : messages;

  const handleSend = () => {
    const text = input.trim();
    if (!text || sendMessage.isPending) return;

    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: text,
      cited_article_ids: [],
      model_used: null,
      created_at: new Date().toISOString(),
    };

    if (!selectedId) {
      setMessages((prev) => [...prev, userMsg]);
    }
    setInput('');

    sendMessage.mutate(
      { message: text, conversation_id: selectedId ?? undefined },
      {
        onSuccess: (response) => {
          if (!selectedId) {
            setMessages((prev) => [...prev, response]);
          }
        },
      },
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    setSelectedId(null);
    setMessages([]);
  };

  return (
    <div className="flex h-[calc(100vh-3.5rem)] gap-4">
      {/* Conversation sidebar */}
      <div className="flex w-64 flex-col rounded-lg border bg-card">
        <div className="flex items-center justify-between p-3">
          <h3 className="text-sm font-medium">Conversations</h3>
          <Button variant="ghost" size="icon" onClick={handleNewChat}>
            <Plus className="size-4" />
          </Button>
        </div>
        <Separator />
        <ScrollArea className="flex-1">
          <div className="space-y-1 p-2">
            {conversations.length === 0 && (
              <p className="px-2 py-4 text-center text-xs text-muted-foreground">
                No conversations yet
              </p>
            )}
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setSelectedId(conv.id)}
                className={cn(
                  'flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-sm transition-colors',
                  selectedId === conv.id
                    ? 'bg-accent text-accent-foreground'
                    : 'hover:bg-muted',
                )}
              >
                <span className="truncate">
                  {conv.title ?? 'Untitled'}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-6 shrink-0 opacity-0 group-hover:opacity-100"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation.mutate(conv.id);
                    if (selectedId === conv.id) handleNewChat();
                  }}
                >
                  <Trash2 className="size-3" />
                </Button>
              </button>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Chat area */}
      <div className="flex flex-1 flex-col rounded-lg border bg-card">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {displayMessages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 text-center text-muted-foreground">
                <p className="text-lg font-medium">News Copilot</p>
                <p className="mt-1 text-sm">
                  Ask questions about the news articles in your dashboard.
                </p>
              </div>
            )}
            {displayMessages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  'flex flex-col gap-1',
                  msg.role === 'user' ? 'items-end' : 'items-start',
                )}
              >
                <span className="text-xs text-muted-foreground">
                  {msg.role === 'user' ? 'You' : 'Assistant'}
                </span>
                <div
                  className={cn(
                    'max-w-[70%] rounded-lg px-4 py-2 text-sm',
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted',
                  )}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  {msg.cited_article_ids.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {msg.cited_article_ids.map((_, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          [{i + 1}]
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {sendMessage.isPending && (
              <div className="flex items-start">
                <div className="rounded-lg bg-muted px-4 py-2 text-sm text-muted-foreground">
                  Thinking...
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <Separator />
        <div className="p-4">
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about the news..."
              className="min-h-[44px] max-h-[120px] resize-none"
              rows={1}
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || sendMessage.isPending}
            >
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
