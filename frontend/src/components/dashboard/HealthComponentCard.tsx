import React from 'react';
import { ComponentStatus } from '../../types/api';
import { StatusIndicator } from '../common/StatusIndicator';
import { Database, Cpu, Sparkles, Server } from 'lucide-react';

interface HealthComponentCardProps {
  name: string;
  component?: ComponentStatus;
}

export const HealthComponentCard: React.FC<HealthComponentCardProps> = ({
  name,
  component,
}) => {
  if (!component) return null;

  const getInfo = () => {
    switch (name) {
      case 'vector_storage':
        return {
          title: 'Persistent Qdrant Vector Storage',
          icon: Database,
          desc: 'On-disk file-backed vector database storing dense embeddings',
        };
      case 'embeddings':
        return {
          title: 'Sentence-Transformers Embedding Engine',
          icon: Cpu,
          desc: 'Local dense vector encoder running on CPU/MPS Metal',
        };
      case 'llm_engine':
        return {
          title: 'Ollama Local LLM Engine',
          icon: Sparkles,
          desc: 'Quantized generative model for synthesis & adaptive reasoning',
        };
      default:
        return {
          title: name.replace('_', ' ').toUpperCase(),
          icon: Server,
          desc: 'System component',
        };
    }
  };

  const { title, icon: Icon, desc } = getInfo();

  return (
    <div className="p-5 rounded-2xl bg-surface-card border border-surface-border shadow-sm flex flex-col justify-between space-y-4">
      <div>
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center text-indigo-400 shrink-0">
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-100">{title}</h4>
              <p className="text-[11px] text-slate-400">{desc}</p>
            </div>
          </div>
          <StatusIndicator status={component.status} label={component.status} size="sm" />
        </div>

        {/* Details Grid */}
        <div className="mt-4 pt-4 border-t border-surface-border/60 grid grid-cols-2 gap-2 text-xs font-mono">
          {Object.entries(component.details).map(([key, val]) => (
            <div
              key={key}
              className="p-2.5 rounded-lg bg-surface/50 border border-surface-border/50 min-w-0"
            >
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block truncate">
                {key.replace(/_/g, ' ')}
              </span>
              <span className="text-slate-200 text-xs font-semibold block truncate mt-0.5">
                {typeof val === 'object' && val !== null
                  ? JSON.stringify(val)
                  : String(val)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="pt-2 text-[10px] text-slate-500 font-mono">
        Reported via /api/v1/health
      </div>
    </div>
  );
};
