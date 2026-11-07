import React from 'react';
import { RotateCcw } from 'lucide-react';

interface QueryRewriteHistoryProps {
  originalQuery: string;
  rewrittenQueries: string[];
  retrievalAttempts: number;
}

export const QueryRewriteHistory: React.FC<QueryRewriteHistoryProps> = ({
  originalQuery,
  rewrittenQueries,
  retrievalAttempts,
}) => {
  if (!rewrittenQueries || rewrittenQueries.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-surface/50 border border-surface-border text-center text-xs text-slate-500 font-mono">
        No query rewrites required. Initial retrieval provided sufficient relevant evidence.
      </div>
    );
  }

  return (
    <div className="p-5 rounded-2xl bg-surface-card border border-surface-border shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-amber-950/80 border border-amber-800/60 flex items-center justify-center text-amber-400">
            <RotateCcw className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              Adaptive Query Reformulation
            </h4>
            <p className="text-xs text-slate-400">
              Resolved conversational noise and vocabulary mismatch
            </p>
          </div>
        </div>

        <span className="px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-amber-950/60 text-amber-300 border border-amber-800/60">
          {rewrittenQueries.length} Rewrite{rewrittenQueries.length > 1 ? 's' : ''} ({retrievalAttempts} Cycles)
        </span>
      </div>

      <div className="space-y-3">
        {/* Original Query */}
        <div className="p-3 rounded-xl bg-surface/60 border border-surface-border text-xs">
          <span className="text-[10px] font-mono uppercase text-slate-500 font-semibold block mb-1">
            Original User Question
          </span>
          <p className="text-slate-300 font-mono italic">"{originalQuery}"</p>
        </div>

        {/* Reformulations */}
        <div className="space-y-2">
          {rewrittenQueries.map((rewrite, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl bg-indigo-950/20 border border-indigo-900/40 text-xs flex items-start gap-2.5"
            >
              <div className="w-5 h-5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-800/60 flex items-center justify-center text-[10px] font-mono font-bold shrink-0 mt-0.5">
                {idx + 1}
              </div>
              <div className="flex-1">
                <span className="text-[10px] font-mono uppercase text-indigo-400 font-semibold block mb-0.5">
                  Attempt #{idx + 1} Reformulation
                </span>
                <p className="text-slate-200 font-mono leading-relaxed">
                  "{rewrite}"
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
