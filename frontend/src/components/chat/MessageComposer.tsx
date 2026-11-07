import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  SlidersHorizontal,
  Sparkles,
  Trash2,
  ChevronDown,
  RotateCcw,
} from 'lucide-react';
import { useChatStore } from '../../store/useChatStore';
import { useKnowledgeStore } from '../../store/useKnowledgeStore';
import { RetrievalStrategy, RoutingMode } from '../../types/api';

export const MessageComposer: React.FC = () => {
  const [input, setInput] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    sendMessage,
    isLoading,
    routingMode,
    setRoutingMode,
    retrievalStrategy,
    setRetrievalStrategy,
    adaptive,
    setAdaptive,
    topK,
    setTopK,
    rerank,
    setRerank,
    selectedDocIdFilter,
    setSelectedDocIdFilter,
    clearMessages,
    messages,
  } = useChatStore();

  const { documents } = useKnowledgeStore();

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        180
      )}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-surface-border bg-surface-muted/95 backdrop-blur-md p-4 sticky bottom-0 z-10">
      <div className="max-w-4xl mx-auto space-y-3">
        {/* Controls Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            {/* Routing Mode Selector */}
            <div className="relative">
              <select
                value={routingMode}
                onChange={(e) => setRoutingMode(e.target.value as RoutingMode)}
                className="appearance-none bg-surface-card border border-surface-border rounded-lg pl-2.5 pr-7 py-1 text-slate-200 text-xs font-medium focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                <option value="auto">Route: Auto</option>
                <option value="document_only">Route: Documents Only</option>
                <option value="sql_only">Route: SQL Catalog Only</option>
                <option value="web_only">Route: Web Search Only</option>
                <option value="multi_source">Route: Multi-Source</option>
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            {/* Retrieval Strategy Selector */}
            <div className="relative">
              <select
                value={retrievalStrategy}
                onChange={(e) =>
                  setRetrievalStrategy(e.target.value as RetrievalStrategy)
                }
                className="appearance-none bg-surface-card border border-surface-border rounded-lg pl-2.5 pr-7 py-1 text-slate-200 text-xs font-medium focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                <option value="hybrid">Strategy: Hybrid (Dense+BM25)</option>
                <option value="hybrid_rerank">Strategy: Hybrid + Rerank</option>
                <option value="baseline">Strategy: Dense Baseline</option>
                <option value="multi_query">Strategy: Multi-Query</option>
                <option value="hyde">Strategy: HyDE Synthesis</option>
                <option value="decomposition">Strategy: Decomposition</option>
                <option value="fusion">Strategy: RAG Fusion</option>
                <option value="rerank">Strategy: Cross-Encoder</option>
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            {/* Adaptive RAG Toggle */}
            <button
              type="button"
              onClick={() => setAdaptive(!adaptive)}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium transition-colors ${
                adaptive
                  ? 'bg-violet-950/80 text-violet-300 border-violet-700/70 shadow-sm'
                  : 'bg-surface-card text-slate-400 border-surface-border hover:text-slate-200'
              }`}
              title="Phase 4 LangGraph Adaptive & Corrective RAG (Relevance Grading, Query Rewriting, Grounding Validation)"
            >
              <Sparkles className="w-3 h-3 text-violet-400" />
              <span>Adaptive RAG</span>
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  adaptive ? 'bg-violet-400' : 'bg-slate-600'
                }`}
              />
            </button>

            {/* Advanced Filters Button */}
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border text-xs font-medium transition-colors ${
                showAdvanced || selectedDocIdFilter || rerank
                  ? 'bg-indigo-950/60 text-indigo-300 border-indigo-700/60'
                  : 'bg-surface-card text-slate-400 border-surface-border hover:text-slate-200'
              }`}
              title="Toggle advanced retrieval parameters"
            >
              <SlidersHorizontal className="w-3 h-3" />
              <span>Options</span>
              {(selectedDocIdFilter || rerank) && (
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
              )}
            </button>
          </div>

          {/* Right Actions */}
          {messages.length > 0 && (
            <button
              type="button"
              onClick={clearMessages}
              className="inline-flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-rose-400 hover:bg-rose-950/20 rounded-lg transition-colors"
              title="Clear current conversation"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Clear Chat</span>
            </button>
          )}
        </div>

        {/* Collapsible Advanced Options Panel */}
        {showAdvanced && (
          <div className="p-3 rounded-xl bg-surface-card border border-surface-border grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs animate-fade-in">
            {/* Top K */}
            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Top K Candidates</span>
                <span className="font-mono text-indigo-300">{topK}</span>
              </div>
              <input
                type="range"
                min={1}
                max={10}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
            </div>

            {/* Cross Encoder Rerank Toggle */}
            <div className="flex items-center justify-between p-2 rounded-lg bg-surface/50 border border-surface-border">
              <div>
                <span className="font-medium text-slate-300 block">Rerank Candidates</span>
                <span className="text-[10px] text-slate-500">Cross-encoder model</span>
              </div>
              <input
                type="checkbox"
                checked={rerank}
                onChange={(e) => setRerank(e.target.checked)}
                className="rounded accent-indigo-500 cursor-pointer w-4 h-4"
              />
            </div>

            {/* Document Filter */}
            <div>
              <span className="text-slate-400 block mb-1">Scope to Document</span>
              <select
                value={selectedDocIdFilter || ''}
                onChange={(e) => setSelectedDocIdFilter(e.target.value || null)}
                className="w-full bg-surface border border-surface-border rounded-lg px-2 py-1 text-slate-200 text-xs font-medium focus:outline-none focus:border-indigo-500 truncate"
              >
                <option value="">All Uploaded Documents</option>
                {documents.map((doc) => (
                  <option key={doc.doc_id} value={doc.doc_id}>
                    {doc.filename}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Text Input & Submit */}
        <form onSubmit={handleSubmit} className="relative flex items-end gap-2">
          <div className="relative flex-1 bg-surface-card border border-surface-border rounded-2xl focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500/30 transition-all shadow-inner">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about documents, SQL catalog, or current events (Enter to send, Shift+Enter for newline)..."
              disabled={isLoading}
              rows={1}
              className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 px-4 py-3 focus:outline-none resize-none max-h-44 disabled:opacity-50"
            />
          </div>

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="h-11 w-11 rounded-2xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white flex items-center justify-center transition-all shadow-sm shrink-0"
            aria-label="Send message"
          >
            {isLoading ? (
              <RotateCcw className="w-5 h-5 animate-spin text-slate-400" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>

        <p className="text-[10px] text-center text-slate-400">
          VeriWeave verifies every claim with grounded inline citations. Never hallucinating unindexed facts.
        </p>
      </div>
    </div>
  );
};
