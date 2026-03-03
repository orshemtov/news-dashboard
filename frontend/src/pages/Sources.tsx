import { useState } from 'react';
import {
  useSources,
  useCreateSource,
  useUpdateSource,
  useDeleteSource,
  useSearchTelegramChannels,
  useChannelSuggestions,
} from '@/hooks/useSources';
import type { Source, ChannelSuggestion } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Loader2,
  Search,
  Trash2,
  X,
  Send as TelegramIcon,
  Plus,
  Check,
  Sparkles,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
  Circle,
  RefreshCw,
} from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

export default function Sources() {
  const { data: sources, isLoading } = useSources();
  const createSource = useCreateSource();
  const updateSource = useUpdateSource();
  const deleteSource = useDeleteSource();

  // Track which specific channel usernames are currently being added
  const [pendingAdds, setPendingAdds] = useState<Set<string>>(new Set());
  // Track which usernames were just successfully added (for instant feedback)
  const [justAdded, setJustAdded] = useState<Set<string>>(new Set());

  // Channel search
  const [searchQuery, setSearchQuery] = useState('');
  const { data: searchResults, isLoading: isSearching } =
    useSearchTelegramChannels(searchQuery);

  // Channel suggestions
  const { data: suggestions, isLoading: isSuggestionsLoading } =
    useChannelSuggestions();
  const [showAllSuggestions, setShowAllSuggestions] = useState(false);

  const sourceList = sources ?? [];
  const existingChannels = new Set(
    sourceList.map((s) => (s.config?.channel as string)?.toLowerCase()),
  );

  const handleToggleEnabled = (source: Source) => {
    updateSource.mutate({
      id: source.id,
      data: { enabled: !source.enabled },
    });
  };

  const handleAddFromSearch = (channel: {
    title: string | null;
    username: string | null;
  }) => {
    const username = channel.username;
    if (!username) return;
    setPendingAdds((prev) => new Set(prev).add(username));
    createSource.mutate(
      {
        name: channel.title || username,
        source_type: 'telegram',
        config: { channel: username },
      },
      {
        onSuccess: () => {
          setJustAdded((prev) => new Set(prev).add(username));
        },
        onSettled: () => {
          setPendingAdds((prev) => {
            const next = new Set(prev);
            next.delete(username);
            return next;
          });
        },
      },
    );
  };

  const handleAddSuggestion = (suggestion: ChannelSuggestion) => {
    const username = suggestion.username;
    setPendingAdds((prev) => new Set(prev).add(username));
    createSource.mutate(
      {
        name: suggestion.name,
        source_type: 'telegram',
        config: { channel: username },
      },
      {
        onSuccess: () => {
          setJustAdded((prev) => new Set(prev).add(username));
        },
        onSettled: () => {
          setPendingAdds((prev) => {
            const next = new Set(prev);
            next.delete(username);
            return next;
          });
        },
      },
    );
  };

  // Filter out already-added channels and ones just added this session
  const filteredSuggestions = (suggestions ?? []).filter(
    (s) => !existingChannels.has(s.username.toLowerCase()) && !justAdded.has(s.username),
  );
  const visibleSuggestions = showAllSuggestions
    ? filteredSuggestions
    : filteredSuggestions.slice(0, 6);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Telegram Sources</h2>
          <p className="text-sm text-muted-foreground">
            {sourceList.length} channel{sourceList.length !== 1 ? 's' : ''}{' '}
            configured
          </p>
        </div>
      </div>

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search Telegram channels to add..."
          className="pl-9 pr-8"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="size-3.5" />
          </button>
        )}
      </div>

      {/* Search results */}
      {searchQuery.trim().length >= 2 && (
        <div className="rounded-md border border-border">
          {isSearching && (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="size-4 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">
                Searching...
              </span>
            </div>
          )}
          {!isSearching && searchResults && searchResults.length === 0 && (
            <p className="py-4 text-center text-sm text-muted-foreground">
              No channels found for "{searchQuery}"
            </p>
          )}
          {!isSearching &&
            searchResults &&
            searchResults.length > 0 &&
            searchResults.map((ch) => {
              const alreadyAdded = existingChannels.has(
                ch.username?.toLowerCase() ?? '',
              );
              return (
                <div
                  key={ch.id ?? ch.username}
                  className="flex items-center justify-between border-b border-border px-3 py-2 last:border-b-0"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <TelegramIcon className="size-3.5 shrink-0 text-blue-500" />
                    <span className="text-sm font-medium truncate">
                      {ch.title || ch.username}
                    </span>
                    {ch.username && (
                      <span className="text-xs text-muted-foreground">
                        @{ch.username}
                      </span>
                    )}
                    {ch.participants_count != null && (
                      <span className="text-xs text-muted-foreground">
                        {ch.participants_count.toLocaleString()} members
                      </span>
                    )}
                  </div>
                  <Button
                    variant={alreadyAdded ? 'ghost' : 'outline'}
                    size="sm"
                    className="h-7 shrink-0"
                    disabled={alreadyAdded || pendingAdds.has(ch.username ?? '') || justAdded.has(ch.username ?? '')}
                    onClick={() => handleAddFromSearch(ch)}
                  >
                    {pendingAdds.has(ch.username ?? '') ? (
                      <Loader2 className="size-3 animate-spin" />
                    ) : alreadyAdded || justAdded.has(ch.username ?? '') ? (
                      <>
                        <Check className="size-3" />
                        Added
                      </>
                    ) : (
                      <>
                        <Plus className="size-3" />
                        Add
                      </>
                    )}
                  </Button>
                </div>
              );
            })}
        </div>
      )}

      {/* Source list */}
      {isLoading && (
        <div className="flex justify-center py-8">
          <Loader2 className="size-5 animate-spin text-muted-foreground" />
        </div>
      )}

      {!isLoading && sourceList.length === 0 && (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No sources configured. Search for Telegram channels above to add one.
        </p>
      )}

      {sourceList.length > 0 && (
        <div className="rounded-md border border-border">
          {sourceList.map((source) => (
            <div
              key={source.id}
              className="flex items-center justify-between border-b border-border px-3 py-2 last:border-b-0"
            >
              <div className="flex items-center gap-3 min-w-0">
                <TelegramIcon className="size-3.5 shrink-0 text-blue-500" />
                <span className="text-sm font-medium truncate">
                  {source.name}
                </span>
                
                <div className="flex items-center gap-1.5 shrink-0">
                  {source.error_message ? (
                    <div className="flex items-center gap-1 rounded-full bg-destructive/10 px-2 py-0.5 text-[10px] font-medium text-destructive">
                      <AlertCircle className="size-2.5" />
                      Error
                    </div>
                  ) : source.enabled ? (
                    <div className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
                      <span className="relative flex h-1.5 w-1.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                      </span>
                      Active
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                      <Circle className="size-2.5" />
                      Off
                    </div>
                  )}
                </div>

                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {source.article_count} articles
                </span>
                <span className="hidden sm:inline text-xs text-muted-foreground whitespace-nowrap italic">
                  {source.last_polled_at
                    ? `last sync: ${new Date(source.last_polled_at).toLocaleTimeString()}`
                    : 'never synced'}
                </span>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs hover:bg-emerald-500/10 hover:text-emerald-600"
                  onClick={() => handleToggleEnabled(source)}
                >
                  {source.enabled ? 'Disable' : 'Enable'}
                </Button>
                
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 hover:bg-destructive/10 group"
                    >
                      <Trash2 className="size-3.5 text-muted-foreground group-hover:text-destructive" />
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Delete Source?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will stop ingesting articles from <strong>{source.name}</strong>. 
                        Existing articles from this source will remain in the database.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        onClick={() => deleteSource.mutate(source.id)}
                      >
                        Delete
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error messages */}
      {sourceList
        .filter((s) => s.error_message)
        .map((s) => (
          <p key={s.id} className="text-xs text-destructive">
            {s.name}: {s.error_message}
          </p>
        ))}

      {/* ── Suggested Channels ──────────────────────────────────────── */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles className="size-4 text-amber-500" />
          <h3 className="text-sm font-semibold">Suggested for you</h3>
          <span className="text-xs text-muted-foreground">
            Based on your reading interests
          </span>
        </div>

        {isSuggestionsLoading && (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="size-4 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">
              Analyzing your interests...
            </span>
          </div>
        )}

        {!isSuggestionsLoading && filteredSuggestions.length === 0 && (
          <p className="py-4 text-center text-sm text-muted-foreground">
            No suggestions available. Add some sources and let articles
            accumulate to get personalized recommendations.
          </p>
        )}

        {!isSuggestionsLoading && filteredSuggestions.length > 0 && (
          <>
            <div className="grid gap-2 sm:grid-cols-2">
              {visibleSuggestions.map((suggestion) => (
                <div
                  key={suggestion.username}
                  className="flex flex-col gap-2 rounded-md border border-border p-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <TelegramIcon className="size-3.5 shrink-0 text-blue-500" />
                        <span className="text-sm font-medium truncate">
                          {suggestion.name}
                        </span>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        @{suggestion.username}
                      </span>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 shrink-0"
                      disabled={pendingAdds.has(suggestion.username)}
                      onClick={() => handleAddSuggestion(suggestion)}
                    >
                      {pendingAdds.has(suggestion.username) ? (
                        <Loader2 className="size-3 animate-spin" />
                      ) : (
                        <>
                          <Plus className="size-3" />
                          Add
                        </>
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {suggestion.description}
                  </p>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                      {suggestion.language.toUpperCase()}
                    </Badge>
                    {suggestion.tags.slice(0, 3).map((tag) => (
                      <Badge
                        key={tag}
                        variant="outline"
                        className="text-[10px] px-1.5 py-0"
                      >
                        {tag}
                      </Badge>
                    ))}
                    {suggestion.similarity_score != null && (
                      <span className="ml-auto text-[10px] text-muted-foreground">
                        {Math.round(suggestion.similarity_score * 100)}% match
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {filteredSuggestions.length > 6 && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-xs"
                onClick={() => setShowAllSuggestions(!showAllSuggestions)}
              >
                {showAllSuggestions ? (
                  <>
                    <ChevronUp className="size-3 mr-1" />
                    Show less
                  </>
                ) : (
                  <>
                    <ChevronDown className="size-3 mr-1" />
                    Show {filteredSuggestions.length - 6} more suggestions
                  </>
                )}
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
