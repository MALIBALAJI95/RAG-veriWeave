import React from 'react';
import { RetrievalStrategy } from '../../types/api';
import { Sparkles, Cpu, GitMerge, FileSearch, Split } from 'lucide-react';

interface StrategyBadgeProps {
  strategy: RetrievalStrategy | string;
  size?: 'sm' | 'md';
}

export const StrategyBadge: React.FC<StrategyBadgeProps> = ({
  strategy,
  size = 'md',
}) => {
  const getStrategyConfig = (s: string) => {
    switch (s) {
      case 'baseline':
        return { label: 'Dense Baseline', icon: Cpu, color: 'text-blue-300 bg-blue-950/40 border-blue-800/50' };
      case 'hybrid':
        return { label: 'Hybrid (Dense+BM25)', icon: GitMerge, color: 'text-indigo-300 bg-indigo-950/40 border-indigo-800/50' };
      case 'hybrid_rerank':
        return { label: 'Hybrid + Rerank', icon: Sparkles, color: 'text-purple-300 bg-purple-950/40 border-purple-800/50' };
      case 'multi_query':
        return { label: 'Multi-Query RRF', icon: FileSearch, color: 'text-cyan-300 bg-cyan-950/40 border-cyan-800/50' };
      case 'hyde':
        return { label: 'HyDE Synthesis', icon: Sparkles, color: 'text-emerald-300 bg-emerald-950/40 border-emerald-800/50' };
      case 'decomposition':
        return { label: 'Query Decomposition', icon: Split, color: 'text-amber-300 bg-amber-950/40 border-amber-800/50' };
      case 'fusion':
        return { label: 'RRF Fusion', icon: GitMerge, color: 'text-rose-300 bg-rose-950/40 border-rose-800/50' };
      case 'rerank':
        return { label: 'Cross-Encoder Rerank', icon: Sparkles, color: 'text-violet-300 bg-violet-950/40 border-violet-800/50' };
      default:
        return { label: s, icon: Cpu, color: 'text-slate-300 bg-slate-800/40 border-slate-700/50' };
    }
  };

  const config = getStrategyConfig(strategy);
  const Icon = config.icon;
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${config.color} ${sizeClasses}`}>
      <Icon className="w-3 h-3" />
      <span>{config.label}</span>
    </span>
  );
};
