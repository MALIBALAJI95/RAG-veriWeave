import React from 'react';
import { GroundingValidationResult } from '../../types/api';
import { ShieldCheck, Check, X, ShieldAlert } from 'lucide-react';

interface GroundingValidationCardProps {
  validation?: GroundingValidationResult | null;
}

export const GroundingValidationCard: React.FC<GroundingValidationCardProps> = ({
  validation,
}) => {
  if (!validation) {
    return (
      <div className="p-4 rounded-xl bg-surface/50 border border-surface-border text-center text-xs text-slate-500 font-mono">
        No grounding validation performed on this response (Adaptive RAG disabled).
      </div>
    );
  }

  return (
    <div className="p-5 rounded-2xl bg-surface-card border border-surface-border shadow-sm space-y-4">
      {/* Title & Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
              validation.is_grounded
                ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800/60'
                : 'bg-rose-950/80 text-rose-400 border-rose-800/60'
            }`}
          >
            {validation.is_grounded ? (
              <ShieldCheck className="w-5 h-5" />
            ) : (
              <ShieldAlert className="w-5 h-5" />
            )}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              {validation.is_grounded ? 'Grounded & Verified' : 'Ungrounded Statements Detected'}
            </h4>
            <p className="text-xs text-slate-400">
              Claim-by-claim verification & citation provenance audit
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`px-2.5 py-1 rounded-full text-xs font-semibold font-mono border ${
              validation.citation_valid
                ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                : 'bg-rose-950/60 text-rose-300 border-rose-800/60'
            }`}
          >
            {validation.citation_valid ? 'Citations Valid' : 'Invalid Citations'}
          </span>
          <span className="text-xs text-slate-500 font-mono">
            Attempt #{validation.attempt_number}
          </span>
        </div>
      </div>

      {/* Validation Reason Summary */}
      {validation.validation_reason && (
        <div className="p-3 rounded-xl bg-surface/60 border border-surface-border text-xs text-slate-300 leading-relaxed font-mono">
          <span className="text-slate-500 block text-[10px] uppercase font-semibold mb-1">
            Audit Reason
          </span>
          {validation.validation_reason}
        </div>
      )}

      {/* Claims Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Supported Claims */}
        <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-900/40 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-emerald-300">
            <span className="flex items-center gap-1.5">
              <Check className="w-4 h-4 text-emerald-400" />
              Verified Claims ({validation.supported_claims.length})
            </span>
          </div>
          {validation.supported_claims.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No verified claims recorded</p>
          ) : (
            <ul className="space-y-1.5 text-xs text-slate-300">
              {validation.supported_claims.map((claim, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                  <span className="leading-relaxed">{claim}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Unsupported Claims */}
        <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-900/40 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-rose-300">
            <span className="flex items-center gap-1.5">
              <X className="w-4 h-4 text-rose-400" />
              Unsupported Statements ({validation.unsupported_claims.length})
            </span>
          </div>
          {validation.unsupported_claims.length === 0 ? (
            <p className="text-xs text-emerald-400/90 italic flex items-center gap-1">
              <Check className="w-3.5 h-3.5" />
              Zero unsupported statements or hallucinations detected
            </p>
          ) : (
            <ul className="space-y-1.5 text-xs text-rose-300">
              {validation.unsupported_claims.map((claim, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1.5 shrink-0" />
                  <span className="leading-relaxed">{claim}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};
