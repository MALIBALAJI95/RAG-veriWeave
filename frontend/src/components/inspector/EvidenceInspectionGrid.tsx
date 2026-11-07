import React, { useState } from 'react';
import { EvidenceItem } from '../../types/api';
import { FileText, Database, Globe, ExternalLink } from 'lucide-react';
import { SourceDetailDrawer } from '../chat/SourceDetailDrawer';

interface EvidenceInspectionGridProps {
  evidence: EvidenceItem[];
}

export const EvidenceInspectionGrid: React.FC<EvidenceInspectionGridProps> = ({
  evidence,
}) => {
  const [selectedItem, setSelectedItem] = useState<EvidenceItem | null>(null);

  if (!evidence || evidence.length === 0) {
    return (
      <div className="p-8 rounded-2xl bg-surface/50 border border-surface-border text-center text-xs text-slate-500 font-mono">
        No evidence items retrieved for this query.
      </div>
    );
  }

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'structured_sql':
        return Database;
      case 'web_search':
        return Globe;
      default:
        return FileText;
    }
  };

  const getSourceBadge = (sourceType: string) => {
    switch (sourceType) {
      case 'structured_sql':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/60';
      case 'web_search':
        return 'bg-cyan-950/80 text-cyan-300 border-cyan-800/60';
      default:
        return 'bg-indigo-950/80 text-indigo-300 border-indigo-800/60';
    }
  };

  return (
    <>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
            Unified Evidence Items ({evidence.length})
          </h4>
          <span className="text-[11px] text-slate-500 font-mono">
            Cross-Source Normalization
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {evidence.map((item, idx) => {
            const Icon = getSourceIcon(item.source_type);
            const badgeStyle = getSourceBadge(item.source_type);
            const title =
              item.title || item.filename || item.source_id || 'Evidence';

            return (
              <div
                key={item.evidence_id || idx}
                onClick={() => setSelectedItem(item)}
                className="p-4 rounded-xl bg-surface-card border border-surface-border hover:border-indigo-500/50 hover:bg-surface-hover/70 transition-all cursor-pointer group shadow-sm flex flex-col justify-between"
              >
                <div>
                  {/* Top Bar */}
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono uppercase font-bold border ${badgeStyle}`}
                    >
                      <Icon className="w-3 h-3" />
                      <span>{item.source_type.replace('_', ' ')}</span>
                    </span>

                    <span className="text-xs font-mono font-semibold text-slate-300">
                      Score: {(item.score * 100).toFixed(1)}%
                    </span>
                  </div>

                  {/* Title & Provenance */}
                  <h5 className="text-sm font-semibold text-slate-200 line-clamp-1 group-hover:text-indigo-300 transition-colors mb-1">
                    {title}
                  </h5>

                  <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-400 font-mono mb-3">
                    {item.page_number && (
                      <span>Page {item.page_number}</span>
                    )}
                    {item.chunk_index !== null && item.chunk_index !== undefined && (
                      <span>• Chunk #{item.chunk_index + 1}</span>
                    )}
                    {item.record_id && (
                      <span>• Record #{item.record_id}</span>
                    )}
                  </div>

                  {/* Excerpt */}
                  <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed italic bg-surface/50 p-2.5 rounded-lg border border-slate-800/60 font-mono mb-2">
                    "{item.content_excerpt}"
                  </p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-surface-border/60 text-[10px] text-slate-500 font-mono">
                  <span className="truncate max-w-[180px]">{item.source_id}</span>
                  <span className="text-indigo-400 group-hover:underline flex items-center gap-1">
                    <span>Inspect</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <SourceDetailDrawer
        citation={null}
        evidenceItem={selectedItem}
        onClose={() => setSelectedItem(null)}
      />
    </>
  );
};
