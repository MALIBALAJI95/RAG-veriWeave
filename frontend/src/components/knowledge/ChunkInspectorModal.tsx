import React, { useState } from 'react';
import { X, Search, FileText, Split } from 'lucide-react';
import { useKnowledgeStore } from '../../store/useKnowledgeStore';
import { LoadingSkeleton } from '../common/LoadingSkeleton';

export const ChunkInspectorModal: React.FC = () => {
  const [filterText, setFilterText] = useState('');
  const { selectedDoc, selectedDocChunks, isLoadingChunks, closeInspector } = useKnowledgeStore();

  if (!selectedDoc) return null;

  const filteredChunks = selectedDocChunks.filter((chunk) =>
    chunk.text.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="bg-surface-card border border-surface-border rounded-2xl max-w-4xl w-full h-[85vh] flex flex-col shadow-2xl relative overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-surface-border flex items-center justify-between bg-surface/60">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center text-indigo-400 shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h3 className="text-base font-semibold text-slate-100 truncate">
                {selectedDoc.filename}
              </h3>
              <div className="flex items-center gap-2 text-xs text-slate-400 font-mono mt-0.5">
                <span>{selectedDoc.chunk_count} Chunks</span>
                <span>•</span>
                <span>{selectedDoc.page_count} Pages</span>
                <span>•</span>
                <span className="truncate">ID: {selectedDoc.doc_id}</span>
              </div>
            </div>
          </div>

          <button
            onClick={closeInspector}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-surface-hover transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filter Input */}
        <div className="p-4 border-b border-surface-border bg-surface/40 flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder="Search across extracted chunks..."
              className="w-full bg-surface border border-surface-border rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <span className="text-xs text-slate-400 font-mono shrink-0">
            Showing {filteredChunks.length} of {selectedDocChunks.length} chunks
          </span>
        </div>

        {/* Chunk List */}
        <div className="flex-1 p-5 overflow-y-auto space-y-4">
          {isLoadingChunks ? (
            <LoadingSkeleton count={4} className="h-28" />
          ) : filteredChunks.length === 0 ? (
            <div className="text-center py-16 text-slate-400">
              <Split className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              <p className="text-sm">No chunks found matching "{filterText}".</p>
            </div>
          ) : (
            filteredChunks.map((chunk) => (
              <div
                key={chunk.chunk_id}
                className="p-4 rounded-xl bg-surface border border-surface-border hover:border-slate-700 transition-colors shadow-sm"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2 pb-2 border-b border-surface-border/60 text-xs font-mono text-slate-400">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800/60 font-semibold">
                      Chunk #{chunk.chunk_index + 1}
                    </span>
                    <span className="text-slate-300">
                      Page {chunk.page_number}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-slate-500">
                    <span>Offsets: [{chunk.char_start} : {chunk.char_end}]</span>
                    <span>Tokens: ~{chunk.token_count_estimate}</span>
                    <span className="truncate max-w-[140px] text-slate-600">
                      {chunk.chunk_id}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-200 font-mono leading-relaxed whitespace-pre-wrap selection:bg-indigo-600/30">
                  {chunk.text}
                </p>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-surface-border bg-surface/60 flex justify-end">
          <button
            onClick={closeInspector}
            className="px-4 py-2 bg-surface-hover hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
