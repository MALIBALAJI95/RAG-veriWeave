import React from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { Header } from '../components/common/Header';
import { useChatStore } from '../store/useChatStore';
import { WorkflowTraceGraph } from '../components/inspector/WorkflowTraceGraph';
import { GroundingValidationCard } from '../components/inspector/GroundingValidationCard';
import { QueryRewriteHistory } from '../components/inspector/QueryRewriteHistory';
import { EvidenceInspectionGrid } from '../components/inspector/EvidenceInspectionGrid';
import { RouteBadge } from '../components/common/RouteBadge';
import { StrategyBadge } from '../components/common/StrategyBadge';
import {
  SearchCode,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Sparkles,
  ArrowRight,
  Cpu,
} from 'lucide-react';

interface OutletContextType {
  onMobileMenuOpen: () => void;
}

export const RetrievalInspectorPage: React.FC = () => {
  const { onMobileMenuOpen } = useOutletContext<OutletContextType>();
  const { inspectedResponse, messages, sendMessage, isLoading } = useChatStore();

  // If no inspectedResponse is explicitly chosen, fallback to the latest assistant message response
  const latestResponse =
    inspectedResponse ||
    messages
      .slice()
      .reverse()
      .find((m) => m.sender === 'assistant' && m.responseMetadata)?.responseMetadata
      ?.rawResponse ||
    null;

  if (!latestResponse) {
    return (
      <div className="flex-1 flex flex-col h-full min-w-0 bg-background overflow-hidden">
        <Header
          title="Retrieval Inspector"
          subtitle="Inspect routing decisions, LangGraph state machine trace, evidence grading, and grounding audits"
          onMobileMenuOpen={onMobileMenuOpen}
        />

        <div className="flex-1 flex items-center justify-center p-8 text-center">
          <div className="max-w-md p-8 rounded-3xl bg-surface-card border border-surface-border shadow-xl space-y-5 animate-fade-in">
            <div className="w-14 h-14 rounded-2xl bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center text-indigo-400 mx-auto shadow-glow-primary">
              <SearchCode className="w-7 h-7" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-100">
                No Retrieval Trace to Inspect Yet
              </h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Submit a query in the AI Chat to observe real-time multi-path routing, evidence grading, query reformulation, and hallucination verification.
              </p>
            </div>
            <button
              onClick={() =>
                sendMessage(
                  'What is the difference between short-term memory and long-term memory in AI agents?'
                )
              }
              disabled={isLoading}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-sm"
            >
              <Sparkles className="w-4 h-4" />
              <span>Run Benchmark Query & Inspect</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  const {
    query,
    latency_ms,
    model_used,
    grounded,
    routing_decision,
    retrieval_metadata,
    evidence,
    adaptive_metadata,
  } = latestResponse;

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 bg-background overflow-hidden">
      <Header
        title="Retrieval Inspector"
        subtitle={`Inspecting diagnostics for: "${query.slice(0, 60)}..."`}
        onMobileMenuOpen={onMobileMenuOpen}
      />

      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Query Summary & Decision Bar */}
          <div className="p-6 rounded-2xl bg-surface-card border border-surface-border shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-surface-border">
              <div>
                <span className="text-[10px] uppercase font-mono text-slate-500 font-semibold block mb-1">
                  Active Inspected Inquiry
                </span>
                <h2 className="text-lg font-bold text-slate-100 leading-snug">
                  "{query}"
                </h2>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Link
                  to="/app/chat"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface hover:bg-surface-hover text-xs font-medium text-slate-300 border border-surface-border transition-colors"
                >
                  <span>Return to Chat</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Diagnostic Badges */}
            <div className="flex flex-wrap items-center gap-3">
              {routing_decision && (
                <RouteBadge
                  route={routing_decision.route}
                  confidence={routing_decision.confidence}
                />
              )}
              {retrieval_metadata && (
                <StrategyBadge strategy={retrieval_metadata.strategy} />
              )}
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>{latency_ms.toFixed(1)} ms</span>
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
                <Cpu className="w-3.5 h-3.5 text-slate-400" />
                <span>{model_used}</span>
              </span>
              {grounded ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-800/60">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Fully Grounded</span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/60 text-amber-300 border border-amber-800/60">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span>Extractive Fallback</span>
                </span>
              )}
            </div>

            {/* Routing Decision Rationale */}
            {routing_decision && (
              <div className="p-3.5 rounded-xl bg-surface/60 border border-surface-border text-xs leading-relaxed font-mono text-slate-300">
                <span className="text-slate-500 font-semibold block text-[10px] uppercase mb-1">
                  Router Rationale (Method: {routing_decision.classification_method})
                </span>
                {routing_decision.reasoning}
              </div>
            )}
          </div>

          {/* Section 1: LangGraph Workflow Trace */}
          {adaptive_metadata?.workflow_trace && (
            <div className="p-6 rounded-2xl bg-surface-card border border-surface-border shadow-sm">
              <WorkflowTraceGraph trace={adaptive_metadata.workflow_trace} />
            </div>
          )}

          {/* Section 2: Grounding & Hallucination Audit */}
          <GroundingValidationCard
            validation={adaptive_metadata?.grounding_validation}
          />

          {/* Section 3: Adaptive Query Rewrite Progression */}
          {adaptive_metadata && (
            <QueryRewriteHistory
              originalQuery={adaptive_metadata.original_query}
              rewrittenQueries={adaptive_metadata.rewritten_queries}
              retrievalAttempts={adaptive_metadata.retrieval_attempts}
            />
          )}

          {/* Section 4: Cross-Source Evidence Grid */}
          <EvidenceInspectionGrid evidence={evidence} />
        </div>
      </div>
    </div>
  );
};
