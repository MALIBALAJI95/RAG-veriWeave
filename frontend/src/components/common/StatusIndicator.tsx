import React from 'react';

interface StatusIndicatorProps {
  status: 'ok' | 'healthy' | 'degraded' | 'error' | 'unhealthy' | string;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  size = 'md',
}) => {
  const isHealthy = status === 'ok' || status === 'healthy';
  const isDegraded = status === 'degraded';

  const dotColor = isHealthy
    ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]'
    : isDegraded
    ? 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.6)]'
    : 'bg-rose-400 shadow-[0_0_8px_rgba(248,113,113,0.6)]';

  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5',
    lg: 'w-3 h-3',
  };

  return (
    <div className="inline-flex items-center gap-2">
      <span className={`inline-block rounded-full ${sizeClasses[size]} ${dotColor}`} />
      {label && (
        <span className="text-xs font-medium text-slate-300 capitalize">
          {label}
        </span>
      )}
    </div>
  );
};
