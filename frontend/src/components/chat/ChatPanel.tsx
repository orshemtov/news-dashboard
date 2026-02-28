import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, MessageSquare, X, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { useSendMessage, useChatConfig } from '@/hooks/useChat';
import type { ChatMessage } from '@/types';

const LS_PROVIDER_KEY = 'news-dashboard-chat-provider';
const LS_MODEL_KEY = 'news-dashboard-chat-model';

function getStoredProvider(): string | null {
  try { return localStorage.getItem(LS_PROVIDER_KEY); } catch { return null; }
}
function getStoredModel(): string | null {
  try { return localStorage.getItem(LS_MODEL_KEY); } catch { return null; }
}

export function ChatPanel() {
  const [open, setOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sendMessage = useSendMessage();
  const { data: chatConfig } = useChatConfig();

  // Provider/model state — initialised from localStorage, falls back to server defaults
  const [selectedProvider, setSelectedProvider] = useState<string | null>(getStoredProvider);
  const [selectedModel, setSelectedModel] = useState<string | null>(getStoredModel);

  // Resolve effective provider & model against config
  const effectiveProvider = selectedProvider ?? chatConfig?.default_provider ?? 'ollama';
  const currentProviderConfig = chatConfig?.providers.find((p) => p.id === effectiveProvider);
  const effectiveModel =
    selectedModel && currentProviderConfig?.models.includes(selectedModel)
      ? selectedModel
      : currentProviderConfig?.models[0] ?? chatConfig?.default_model ?? '';

  // Persist selections
  const handleProviderChange = useCallback((value: string) => {
    setSelectedProvider(value);
    setSelectedModel(null); // reset model when provider changes
    try {
      localStorage.setItem(LS_PROVIDER_KEY, value);
      localStorage.removeItem(LS_MODEL_KEY);
    } catch { /* noop */ }
  }, []);

  const handleModelChange = useCallback((value: string) => {
    setSelectedModel(value);
    try { localStorage.setItem(LS_MODEL_KEY, value); } catch { /* noop */ }
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

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
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    sendMessage.mutate(
      {
        message: text,
        conversation_id: conversationId ?? undefined,
        provider: effectiveProvider,
        model: effectiveModel,
      },
      {
        onSuccess: (response) => {
          setMessages((prev) => [...prev, response]);
          if (!conversationId) {
            setConversationId(response.id);
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

  if (!open) {
    return (
      <Button
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 z-40 size-12 rounded-full shadow-lg sm:bottom-6 sm:right-6"
        size="icon"
      >
        <MessageSquare className="size-5" />
      </Button>
    );
  }

  return (
    <div className="fixed bottom-0 right-0 z-40 flex h-[100dvh] w-full flex-col overflow-hidden border bg-card shadow-2xl sm:bottom-6 sm:right-6 sm:h-[28rem] sm:w-96 sm:rounded-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="size-4 text-primary" />
          <span className="text-sm font-semibold">News Copilot</span>
          {effectiveModel && (
            <span className="text-[10px] text-muted-foreground">
              {effectiveModel}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="size-7"
            onClick={() => setShowSettings((v) => !v)}
          >
            <Settings className={cn('size-3.5', showSettings && 'text-primary')} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="size-7"
            onClick={() => setOpen(false)}
          >
            <X className="size-4" />
          </Button>
        </div>
      </div>

      {/* Settings row */}
      {showSettings && chatConfig && (
        <div className="flex items-center gap-2 border-b px-4 py-2">
          <Select value={effectiveProvider} onValueChange={handleProviderChange}>
            <SelectTrigger className="h-7 w-[8.5rem] text-xs">
              <SelectValue placeholder="Provider" />
            </SelectTrigger>
            <SelectContent>
              {chatConfig.providers.map((p) => (
                <SelectItem key={p.id} value={p.id} className="text-xs">
                  {p.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={effectiveModel} onValueChange={handleModelChange}>
            <SelectTrigger className="h-7 min-w-0 flex-1 text-xs">
              <SelectValue placeholder="Model" />
            </SelectTrigger>
            <SelectContent>
              {currentProviderConfig?.models.map((m) => (
                <SelectItem key={m} value={m} className="text-xs">
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 px-4" ref={scrollRef}>
        <div className="space-y-3 py-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
              <p className="text-sm">
                Ask questions about the news articles.
              </p>
            </div>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                'flex flex-col gap-1',
                msg.role === 'user' ? 'items-end' : 'items-start',
              )}
            >
              <span className="text-[11px] text-muted-foreground">
                {msg.role === 'user' ? 'You' : 'Assistant'}
              </span>
              <div
                className={cn(
                  'max-w-[85%] rounded-lg px-3 py-2 text-sm',
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
              <div className="rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
                Thinking...
              </div>
            </div>
          )}
          {sendMessage.isError && (
            <div className="flex items-start">
              <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                Failed to get a response. Please try again.
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t p-3">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the news..."
            className="min-h-[40px] max-h-[80px] resize-none text-sm"
            rows={1}
          />
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!input.trim() || sendMessage.isPending}
          >
            <Send className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
