import { useState } from 'react';
import {
  useSources,
  useSourcePresets,
  useCreateSource,
  useUpdateSource,
  useDeleteSource,
  useTestSource,
} from '@/hooks/useSources';
import type { Source, SourcePreset } from '@/types';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Plus,
  Trash2,
  Loader2,
  CheckCircle2,
  XCircle,
  Rss,
  Send as TelegramIcon,
} from 'lucide-react';

export default function Sources() {
  const { data: sources, isLoading } = useSources();
  const { data: presets } = useSourcePresets();
  const createSource = useCreateSource();
  const updateSource = useUpdateSource();
  const deleteSource = useDeleteSource();
  const testSource = useTestSource();

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [addType, setAddType] = useState<'rss' | 'telegram'>('rss');
  const [newName, setNewName] = useState('');
  const [newUrl, setNewUrl] = useState('');
  const [newChannelId, setNewChannelId] = useState('');

  const resetForm = () => {
    setNewName('');
    setNewUrl('');
    setNewChannelId('');
    setAddType('rss');
  };

  const handleAddSource = () => {
    const config =
      addType === 'rss'
        ? { url: newUrl }
        : { channel_id: newChannelId };

    createSource.mutate(
      {
        name: newName,
        source_type: addType,
        config,
      },
      {
        onSuccess: () => {
          setAddDialogOpen(false);
          resetForm();
        },
      }
    );
  };

  const handleAddPreset = (preset: SourcePreset) => {
    createSource.mutate({
      name: preset.name,
      source_type: preset.source_type,
      config: preset.config,
    });
  };

  const handleToggleEnabled = (source: Source) => {
    updateSource.mutate({
      id: source.id,
      data: { enabled: !source.enabled },
    });
  };

  const handleTestUrl = () => {
    testSource.mutate({
      source_type: addType,
      config: addType === 'rss' ? { url: newUrl } : { channel_id: newChannelId },
    });
  };

  // Group presets by category
  const presetsByCategory = (presets ?? []).reduce<Record<string, SourcePreset[]>>(
    (acc, p) => {
      const cat = p.category || 'Other';
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(p);
      return acc;
    },
    {}
  );

  // Track which presets are already added as sources
  const sourceNames = new Set((sources ?? []).map((s) => s.name));

  const sourceList = sources ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Configured Sources</h2>
          <p className="text-sm text-muted-foreground">
            {sourceList.length} source{sourceList.length !== 1 ? 's' : ''}{' '}
            configured
          </p>
        </div>
        <Button onClick={() => setAddDialogOpen(true)}>
          <Plus className="size-4" />
          Add Source
        </Button>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Source list */}
      <div className="grid gap-3">
        {sourceList.map((source) => (
          <Card key={source.id} className="py-4">
            <CardHeader className="pb-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {source.source_type === 'rss' ? (
                    <Rss className="size-4 text-orange-500" />
                  ) : (
                    <TelegramIcon className="size-4 text-blue-500" />
                  )}
                  <CardTitle className="text-base">{source.name}</CardTitle>
                  <Badge
                    variant={
                      source.error_message
                        ? 'destructive'
                        : source.enabled
                          ? 'default'
                          : 'secondary'
                    }
                  >
                    {source.error_message
                      ? 'Error'
                      : source.enabled
                        ? 'Active'
                        : 'Disabled'}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggleEnabled(source)}
                  >
                    {source.enabled ? 'Disable' : 'Enable'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => {
                      if (confirm('Delete this source?')) {
                        deleteSource.mutate(source.id);
                      }
                    }}
                  >
                    <Trash2 className="size-4 text-destructive" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-2">
              <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-muted-foreground">
                <span>Type: {source.source_type}</span>
                <span>Articles: {source.article_count}</span>
                <span>
                  Last polled:{' '}
                  {source.last_polled_at
                    ? new Date(source.last_polled_at).toLocaleString()
                    : 'Never'}
                </span>
                <span>
                  Interval: {source.poll_interval_seconds}s
                </span>
              </div>
              {source.error_message && (
                <p className="mt-2 text-sm text-destructive">
                  {source.error_message}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Preset sources – always visible on the page */}
      {Object.keys(presetsByCategory).length > 0 && (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold">Available Presets</h2>
            <p className="text-sm text-muted-foreground">
              Quick-add from curated news sources
            </p>
          </div>
          {Object.entries(presetsByCategory).map(
            ([category, categoryPresets]) => (
              <div key={category} className="space-y-2">
                <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                  {category}
                </h3>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {categoryPresets.map((preset) => {
                    const alreadyAdded = sourceNames.has(preset.name);
                    return (
                      <Card
                        key={preset.name}
                        className="py-3"
                      >
                        <CardContent className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3 min-w-0">
                            {preset.source_type === 'rss' ? (
                              <Rss className="size-4 shrink-0 text-orange-500" />
                            ) : (
                              <TelegramIcon className="size-4 shrink-0 text-blue-500" />
                            )}
                            <div className="min-w-0">
                              <p className="text-sm font-medium truncate">
                                {preset.name}
                              </p>
                              <p className="text-xs text-muted-foreground truncate">
                                {preset.description}
                              </p>
                            </div>
                          </div>
                          <Button
                            variant={alreadyAdded ? 'ghost' : 'outline'}
                            size="sm"
                            onClick={() => handleAddPreset(preset)}
                            disabled={alreadyAdded || createSource.isPending}
                            className="shrink-0"
                          >
                            {alreadyAdded ? (
                              <CheckCircle2 className="size-4 text-green-500" />
                            ) : (
                              <Plus className="size-4" />
                            )}
                            {alreadyAdded ? 'Added' : 'Add'}
                          </Button>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )
          )}
        </div>
      )}

      {/* Add Source Dialog – for custom sources */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Add Custom Source</DialogTitle>
            <DialogDescription>
              Add a custom RSS feed or Telegram channel
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="max-h-[60vh]">
            <div className="space-y-6 pr-4">
              {/* Source Type */}
              <div className="flex gap-2">
                <Button
                  variant={addType === 'rss' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setAddType('rss')}
                >
                  <Rss className="size-4" />
                  RSS Feed
                </Button>
                <Button
                  variant={addType === 'telegram' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setAddType('telegram')}
                >
                  <TelegramIcon className="size-4" />
                  Telegram
                </Button>
              </div>

              {/* Form */}
              <div className="space-y-3">
                <Input
                  placeholder="Source name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                />

                {addType === 'rss' ? (
                  <div className="flex gap-2">
                    <Input
                      placeholder="RSS feed URL"
                      value={newUrl}
                      onChange={(e) => setNewUrl(e.target.value)}
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleTestUrl}
                      disabled={!newUrl || testSource.isPending}
                    >
                      {testSource.isPending ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        'Test'
                      )}
                    </Button>
                  </div>
                ) : (
                  <Input
                    placeholder="Telegram channel ID or username"
                    value={newChannelId}
                    onChange={(e) => setNewChannelId(e.target.value)}
                  />
                )}

                {testSource.data && (
                  <div className="flex items-center gap-2 text-sm">
                    {testSource.data.success ? (
                      <>
                        <CheckCircle2 className="size-4 text-green-500" />
                        <span className="text-green-600">
                          {testSource.data.message} (
                          {testSource.data.sample_items.length} items found)
                        </span>
                      </>
                    ) : (
                      <>
                        <XCircle className="size-4 text-destructive" />
                        <span className="text-destructive">
                          {testSource.data.message}
                        </span>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          </ScrollArea>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setAddDialogOpen(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddSource}
              disabled={
                !newName ||
                (addType === 'rss' ? !newUrl : !newChannelId) ||
                createSource.isPending
              }
            >
              {createSource.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Plus className="size-4" />
              )}
              Add Source
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
