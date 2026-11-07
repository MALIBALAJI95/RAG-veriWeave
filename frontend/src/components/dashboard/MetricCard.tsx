import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  badge?: string;
  badgeColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  badge,
  badgeColor = 'bg-slate-800 text-slate-300 border-slate-700',
}) => {
  return (
    <div className="p-5 rounded-2xl bg-surface-card border border-surface-border shadow-sm flex flex-col justify-between">
      <div className="flex items-center justify-between gap-2 mb-3">
        <span className="text-xs font-semibold text-slate-400 font-mono uppercase tracking-wider">
          {title}
        </span>
        <div className="w-8 h-8 rounded-xl bg-surface-hover/70 flex items-center justify-center text-indigo-400 border border-surface-border">
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <span className="text-2xl font-bold font-mono text-slate-100 tracking-tight">
          {value}
        </span>
        {badge && (
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${badgeColor}`}
          >
            {badge}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="text-[11px] text-slate-500 mt-2 truncate font-mono">
          {subtitle}
        </p>
      )}
    </div>
  );
};
