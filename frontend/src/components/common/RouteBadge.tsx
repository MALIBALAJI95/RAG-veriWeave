import React from 'react';
import { RouteCategory } from '../../types/api';
import { Database, FileText, Globe, Layers } from 'lucide-react';

interface RouteBadgeProps {
  route: RouteCategory | string;
  confidence?: number;
  size?: 'sm' | 'md';
}

export const RouteBadge: React.FC<RouteBadgeProps> = ({
  route,
  confidence,
  size = 'md',
}) => {
  const getRouteConfig = (r: string) => {
    switch (r) {
      case 'vector_document':
        return {
          label: 'Vector Docs',
          icon: FileText,
          bg: 'bg-indigo-950/60',
          text: 'text-indigo-300',
          border: 'border-indigo-800/60',
        };
      case 'structured_sql':
        return {
          label: 'Structured SQL',
          icon: Database,
          bg: 'bg-emerald-950/60',
          text: 'text-emerald-300',
          border: 'border-emerald-800/60',
        };
      case 'web_search':
        return {
          label: 'Web Search',
          icon: Globe,
          bg: 'bg-cyan-950/60',
          text: 'text-cyan-300',
          border: 'border-cyan-800/60',
        };
      case 'multi_source':
        return {
          label: 'Multi-Source',
          icon: Layers,
          bg: 'bg-violet-950/60',
          text: 'text-violet-300',
          border: 'border-violet-800/60',
        };
      default:
        return {
          label: r,
          icon: Layers,
          bg: 'bg-slate-800/60',
          text: 'text-slate-300',
          border: 'border-slate-700/60',
        };
    }
  };

  const config = getRouteConfig(route);
  const Icon = config.icon;

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${config.border} ${config.bg} ${config.text} ${sizeClasses}`}
    >
      <Icon className="w-3.5 h-3.5" />
      <span>{config.label}</span>
      {confidence !== undefined && (
        <span className="opacity-75 font-mono text-[10px]">
          ({Math.round(confidence * 100)}%)
        </span>
      )}
    </span>
  );
};
