import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Copy,
  Check,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Cpu,
  Layers,
  Sparkles,
  SearchCode,
  User,
} from 'lucide-react';
import { ChatMessage } from '../../types/chat';
import { Citation } from '../../types/api';
import { CitationCard } from './CitationCard';
import { RouteBadge } from '../common/RouteBadge';
import { useNavigate } from 'react-router-dom';
import { useChatStore } from '../../store/useChatStore';
import { SourceDetailDrawer } from './SourceDetailDrawer';

interface ChatMessageItemProps {
  message: ChatMessage;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const navigate = useNavigate();
  const { setInspectedResponse } = useChatStore();

  const isUser = message.sender === 'user';
  const meta = message.responseMetadata;

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleInspect = () => {
    if (meta?.rawResponse) {
      setInspectedResponse(meta.rawResponse);
      navigate('/app/inspector');
    }
  };

  if (isUser) {
    return (
      <div className="flex justify-end gap-3 mb-6">
        <div className="max-w-2xl bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 shadow-md">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          <span className="text-[10px] text-indigo-200/80 block mt-1.5 text-right font-mono">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300 shrink-0">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="flex justify-start gap-3 mb-8 group animate-fade-in">
        <div className="w-8 h-8 rounded-full bg-surface-card border border-surface-border flex items-center justify-center text-indigo-400 shrink-0 shadow-sm mt-1">
          <Sparkles className="w-4 h-4" />
        </div>

        <div className="flex-1 max-w-3xl">
          {/* Main Bubble */}
          <div className="p-5 rounded-2xl rounded-tl-none bg-surface-card/90 border border-surface-border shadow-md">
            {/* Pending State */}
            {message.isPending ? (
              <div className="flex items-center gap-3 py-2 text-sm text-slate-400">
                <div className="flex gap-1">
                  <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" />
                </div>
                <span className="text-xs font-mono">Retrieving intelligently and reasoning contextually...</span>
              </div>
            ) : message.error ? (
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-900/60 text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{message.error}</span>
              </div>
            ) : (
              <>
                {/* Markdown Answer Content */}
                <div className="prose-dark text-sm leading-relaxed mb-4">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>

                {/* Inline Citations Section */}
                {meta && meta.citations.length > 0 && (
                  <div className="pt-4 border-t border-surface-border mt-4">
                    <div className="flex items-center justify-between mb-2.5">
                      <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-indigo-400" />
                        Grounded Source Citations ({meta.citations.length})
                      </span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      {meta.citations.map((citation) => (
                        <CitationCard
                          key={citation.citation_id}
                          citation={citation}
                          onSelect={setActiveCitation}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Diagnostic Metadata Footer */}
            {meta && (
              <div className="pt-3 border-t border-surface-border/80 mt-4 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
                <div className="flex flex-wrap items-center gap-2">
                  {/* Grounded Status Pill */}
                  {meta.grounded ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-800/60 font-medium">
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      Grounded
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-950/60 text-amber-300 border border-amber-800/60 font-medium">
                      <AlertTriangle className="w-3 h-3 text-amber-400" />
                      Extractive Fallback
                    </span>
                  )}

                  {/* Route Badge */}
                  {meta.routing_decision && (
                    <RouteBadge
                      route={meta.routing_decision.route}
                      confidence={meta.routing_decision.confidence}
                      size="sm"
                    />
                  )}

                  {/* Adaptive LangGraph Badge */}
                  {meta.adaptive_metadata?.adaptive_applied && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-violet-950/60 text-violet-300 border border-violet-800/60 font-medium">
                      <Sparkles className="w-3 h-3 text-violet-400" />
                      Adaptive (
                      {meta.adaptive_metadata.retrieval_attempts} cycle
                      {meta.adaptive_metadata.retrieval_attempts > 1 ? 's' : ''})
                    </span>
                  )}

                  {/* Model & Latency */}
                  <span className="inline-flex items-center gap-1 text-slate-400 font-mono">
                    <Cpu className="w-3 h-3 text-slate-500" />
                    {meta.model_used}
                  </span>
                  <span className="inline-flex items-center gap-1 text-slate-400 font-mono">
                    <Clock className="w-3 h-3 text-slate-500" />
                    {meta.latency_ms.toFixed(0)}ms
                  </span>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-1.5 opacity-90 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={handleCopy}
                    className="p-1.5 rounded-lg hover:bg-surface-hover text-slate-400 hover:text-white transition-colors"
                    title="Copy Answer"
                  >
                    {copied ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                  <button
                    onClick={handleInspect}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-surface-hover text-slate-400 hover:text-indigo-300 transition-colors"
                    title="Inspect in Retrieval Inspector"
                  >
                    <SearchCode className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Inspect</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Slide-over Drawer for Citation Source Details */}
      <SourceDetailDrawer
        citation={activeCitation}
        onClose={() => setActiveCitation(null)}
      />
    </>
  );
};
