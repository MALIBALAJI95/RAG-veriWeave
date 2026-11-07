import React from 'react';
import { CheckCircle2 } from 'lucide-react';

interface WorkflowTraceGraphProps {
  trace: string[];
}

export const WorkflowTraceGraph: React.FC<WorkflowTraceGraphProps> = ({ trace }) => {
  if (!trace || trace.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-surface/50 border border-surface-border text-center text-xs text-slate-500 font-mono">
        No LangGraph workflow trace available for this response.
      </div>
    );
  }

  const getNodeInfo = (step: string) => {
    if (step.startsWith('route_query')) {
      return {
        label: 'Route Query',
        desc: step.replace('route_query:', '').trim(),
        color: 'border-indigo-600/70 bg-indigo-950/40 text-indigo-300',
        badge: 'Route',
      };
    }
    if (step.startsWith('retrieve_evidence')) {
      return {
        label: 'Retrieve Evidence',
        desc: step.replace('retrieve_evidence:', '').trim(),
        color: 'border-blue-600/70 bg-blue-950/40 text-blue-300',
        badge: 'Retrieve',
      };
    }
    if (step.startsWith('grade_evidence')) {
      return {
        label: 'Grade Evidence',
        desc: step.replace('grade_evidence:', '').trim(),
        color: 'border-emerald-600/70 bg-emerald-950/40 text-emerald-300',
        badge: 'Grade',
      };
    }
    if (step.startsWith('rewrite_query')) {
      return {
        label: 'Rewrite Query',
        desc: step.replace('rewrite_query:', '').trim(),
        color: 'border-amber-600/70 bg-amber-950/40 text-amber-300',
        badge: 'Loop',
      };
    }
    if (step.startsWith('generate_answer')) {
      return {
        label: 'Generate Answer',
        desc: step.replace('generate_answer:', '').trim(),
        color: 'border-purple-600/70 bg-purple-950/40 text-purple-300',
        badge: 'Synthesize',
      };
    }
    if (step.startsWith('validate_grounding')) {
      return {
        label: 'Validate Grounding',
        desc: step.replace('validate_grounding:', '').trim(),
        color: 'border-cyan-600/70 bg-cyan-950/40 text-cyan-300',
        badge: 'Audit',
      };
    }
    if (step.startsWith('revise_answer')) {
      return {
        label: 'Revise Answer',
        desc: step.replace('revise_answer:', '').trim(),
        color: 'border-rose-600/70 bg-rose-950/40 text-rose-300',
        badge: 'Correct',
      };
    }
    if (step.startsWith('finalize_response')) {
      return {
        label: 'Finalize Response',
        desc: 'Completed verified response packaging',
        color: 'border-emerald-500 bg-emerald-950/50 text-emerald-300',
        badge: 'Done',
      };
    }
    return {
      label: step,
      desc: '',
      color: 'border-slate-700 bg-surface text-slate-300',
      badge: 'Step',
    };
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-1">
        <h4 className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
          LangGraph Execution Trace ({trace.length} Node Transitions)
        </h4>
        <span className="text-[11px] text-slate-500 font-mono">Sequential Flow</span>
      </div>

      <div className="flex flex-col gap-2">
        {trace.map((step, idx) => {
          const info = getNodeInfo(step);
          const isLast = idx === trace.length - 1;

          return (
            <div key={idx} className="flex items-start gap-3 relative">
              {/* Step Number Dot */}
              <div className="flex flex-col items-center">
                <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[11px] font-mono font-semibold text-slate-300 shrink-0">
                  {idx + 1}
                </div>
                {!isLast && (
                  <div className="w-0.5 h-6 bg-slate-800 my-0.5" />
                )}
              </div>

              {/* Step Card */}
              <div
                className={`flex-1 p-3 rounded-xl border ${info.color} shadow-sm transition-all`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold">{info.label}</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono uppercase tracking-wider bg-black/40 border border-white/10">
                      {info.badge}
                    </span>
                  </div>
                  {isLast && (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  )}
                </div>
                {info.desc && (
                  <p className="text-xs text-slate-300/90 font-mono mt-1 leading-relaxed">
                    {info.desc}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
