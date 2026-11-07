import React from 'react';
import { Citation } from '../../types/api';
import { FileText, Database, Globe, Bookmark } from 'lucide-react';

interface CitationCardProps {
  citation: Citation;
  onSelect?: (citation: Citation) => void;
  compact?: boolean;
}

export const CitationCard: React.FC<CitationCardProps> = ({
  citation,
  onSelect,
  compact = false,
}) => {
  const isSQL = citation.filename.toLowerCase().includes('database') || citation.filename.toLowerCase().includes('sql');
  const isWeb = citation.filename.toLowerCase().includes('web:');

  const Icon = isSQL ? Database : isWeb ? Globe : FileText;

  const badgeColor = isSQL
    ? 'bg-emerald-950 text-emerald-300 border-emerald-800/60'
    : isWeb
    ? 'bg-cyan-950 text-cyan-300 border-cyan-800/60'
    : 'bg-indigo-950 text-indigo-300 border-indigo-800/60';

  if (compact) {
    return (
      <button
        onClick={() => onSelect?.(citation)}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono bg-surface-card hover:bg-surface-hover border border-surface-border transition-colors text-slate-300 hover:text-white"
        title={`[${citation.citation_id}] ${citation.filename} (Score: ${(citation.score * 100).toFixed(1)}%)`}
      >
        <Bookmark className="w-3 h-3 text-indigo-400" />
        <span>[{citation.citation_id}]</span>
        <span className="truncate max-w-[120px]">{citation.filename}</span>
      </button>
    );
  }

  return (
    <div
      onClick={() => onSelect?.(citation)}
      className="p-3.5 rounded-xl bg-surface-card/90 border border-surface-border hover:border-indigo-500/40 hover:bg-surface-hover/60 transition-all cursor-pointer group shadow-sm"
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className={`w-5 h-5 rounded flex items-center justify-center text-[10px] font-mono font-bold border shrink-0 ${badgeColor}`}
          >
            {citation.citation_id}
          </span>
          <Icon className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="text-xs font-semibold text-slate-200 truncate group-hover:text-indigo-300 transition-colors">
            {citation.filename}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {citation.page_number > 0 && !isSQL && !isWeb && (
            <span className="text-[11px] text-slate-400 font-mono">
              p. {citation.page_number}
            </span>
          )}
          <span className="text-[11px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
            {Math.round(citation.score * 100)}%
          </span>
        </div>
      </div>
      <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed italic bg-surface/50 p-2 rounded-lg border border-slate-800/60 font-mono">
        "{citation.snippet}"
      </p>
    </div>
  );
};
