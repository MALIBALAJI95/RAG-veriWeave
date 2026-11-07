import React from 'react';
import { Citation, EvidenceItem } from '../../types/api';
import { X, FileText, Database, Globe, Bookmark, ExternalLink } from 'lucide-react';

interface SourceDetailDrawerProps {
  citation: Citation | null;
  evidenceItem?: EvidenceItem | null;
  onClose: () => void;
}

export const SourceDetailDrawer: React.FC<SourceDetailDrawerProps> = ({
  citation,
  evidenceItem,
  onClose,
}) => {
  if (!citation && !evidenceItem) return null;

  const title = evidenceItem?.title || citation?.filename || 'Source Evidence';
  const sourceType = evidenceItem?.source_type || 'vector_document';
  const excerpt = evidenceItem?.content_excerpt || citation?.snippet || '';
  const score = evidenceItem?.score ?? citation?.score ?? 1.0;
  const page = evidenceItem?.page_number || citation?.page_number;
  const docId = evidenceItem?.doc_id || citation?.doc_id;

  const isSQL = sourceType === 'structured_sql' || title.toLowerCase().includes('database');
  const isWeb = sourceType === 'web_search' || title.toLowerCase().includes('web:');
  const Icon = isSQL ? Database : isWeb ? Globe : FileText;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg bg-surface-card border-l border-surface-border h-full flex flex-col shadow-2xl p-6 overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 pb-4 border-b border-surface-border">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center text-indigo-400">
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-mono uppercase text-indigo-400 tracking-wider">
                {sourceType.replace('_', ' ')}
              </span>
              <h3 className="text-base font-semibold text-slate-100 line-clamp-1">
                {title}
              </h3>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-surface-hover transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Provenance Metadata */}
        <div className="grid grid-cols-2 gap-3 my-4">
          <div className="p-3 rounded-xl bg-surface/60 border border-surface-border">
            <span className="text-[10px] text-slate-400 uppercase font-mono">
              Relevance Score
            </span>
            <p className="text-sm font-semibold font-mono text-emerald-400 mt-0.5">
              {(score * 100).toFixed(1)}%
            </p>
          </div>
          <div className="p-3 rounded-xl bg-surface/60 border border-surface-border">
            <span className="text-[10px] text-slate-400 uppercase font-mono">
              Source Location
            </span>
            <p className="text-sm font-semibold text-slate-200 mt-0.5 truncate">
              {page ? `Page ${page}` : isSQL ? 'SQL Table' : 'Web URL'}
            </p>
          </div>
          {docId && (
            <div className="col-span-2 p-3 rounded-xl bg-surface/60 border border-surface-border">
              <span className="text-[10px] text-slate-400 uppercase font-mono">
                Document UUID
              </span>
              <p className="text-xs font-mono text-slate-300 mt-0.5 truncate">
                {docId}
              </p>
            </div>
          )}
          {evidenceItem?.url && (
            <div className="col-span-2 p-3 rounded-xl bg-surface/60 border border-surface-border">
              <span className="text-[10px] text-slate-400 uppercase font-mono">
                Source URL
              </span>
              <a
                href={evidenceItem.url}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 mt-0.5 truncate"
              >
                <span className="truncate">{evidenceItem.url}</span>
                <ExternalLink className="w-3 h-3 shrink-0" />
              </a>
            </div>
          )}
        </div>

        {/* Full Text Content */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Bookmark className="w-3.5 h-3.5 text-indigo-400" />
              Verified Excerpt Content
            </span>
          </div>
          <div className="flex-1 p-4 rounded-xl bg-surface border border-surface-border overflow-y-auto text-sm text-slate-200 font-mono leading-relaxed whitespace-pre-wrap selection:bg-indigo-600/30">
            {excerpt}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-surface-border mt-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-surface-hover hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium transition-colors"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
};
