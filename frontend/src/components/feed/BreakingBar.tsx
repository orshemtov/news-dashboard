import { AlertCircle, X, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { Article } from '@/types';

interface BreakingBarProps {
  burst: {
    lead_article: Article;
    sources: string[];
    count: number;
  };
  onClose: () => void;
  onClick: () => void;
}

export function BreakingBar({ burst, onClose, onClick }: BreakingBarProps) {
  return (
    <div className="relative overflow-hidden rounded-lg border border-red-500/30 bg-red-500/10 p-3 shadow-lg shadow-red-500/5 animate-in fade-in slide-in-from-top-4 duration-500">
      {/* Background Pulse Effect */}
      <div className="absolute inset-0 -z-10 animate-pulse bg-red-500/5" />
      
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-full bg-red-500 p-1 text-white ring-4 ring-red-500/20">
          <AlertCircle className="size-4 animate-bounce" />
        </div>
        
        <div className="flex-1 min-w-0 cursor-pointer" onClick={onClick}>
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-[10px] font-bold uppercase tracking-widest text-red-500">
              Breaking News Burst
            </span>
            <span className="text-[10px] font-medium text-red-500/70">
              • Detected in {burst.sources.length} sources
            </span>
          </div>
          
          <h4 className="text-sm font-semibold leading-snug line-clamp-1 group flex items-center gap-1.5">
            {burst.lead_article.title || burst.lead_article.content.slice(0, 100) + '...'}
            <ExternalLink className="size-3 opacity-0 group-hover:opacity-100 transition-opacity" />
          </h4>
          
          <div className="mt-1.5 flex flex-wrap gap-1">
            {burst.sources.slice(0, 3).map((source) => (
              <span 
                key={source} 
                className="inline-flex items-center rounded-sm bg-red-500/20 px-1.5 py-0.5 text-[10px] font-medium text-red-600"
              >
                {source}
              </span>
            ))}
            {burst.sources.length > 3 && (
              <span className="text-[10px] text-red-500/60 font-medium py-0.5">
                +{burst.sources.length - 3} more
              </span>
            )}
          </div>
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="size-7 -mr-1 -mt-1 text-red-500/50 hover:text-red-500 hover:bg-red-500/10"
          onClick={onClose}
        >
          <X className="size-4" />
        </Button>
      </div>
    </div>
  );
}
