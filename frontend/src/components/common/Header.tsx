import React from 'react';
import { Menu, Sparkles, RefreshCw, Layers } from 'lucide-react';
import { useHealthStore } from '../../store/useHealthStore';
import { StatusIndicator } from './StatusIndicator';
import { Link } from 'react-router-dom';
import { useChatStore } from '../../store/useChatStore';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onMobileMenuOpen?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  onMobileMenuOpen,
}) => {
  const { health, fetchHealth, isLoading } = useHealthStore();
  const { inspectedResponse } = useChatStore();

  return (
    <header className="h-16 px-4 md:px-6 border-b border-surface-border bg-surface/70 backdrop-blur-md flex items-center justify-between shrink-0 sticky top-0 z-20">
      <div className="flex items-center gap-3">
        {onMobileMenuOpen && (
          <button
            onClick={onMobileMenuOpen}
            className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-surface-hover"
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <div>
          <h1 className="text-base md:text-lg font-semibold text-slate-100 flex items-center gap-2">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-slate-400 hidden sm:block">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Latest Response Inspector Pill */}
        {inspectedResponse && (
          <Link
            to="/app/inspector"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-card hover:bg-surface-hover text-xs font-medium text-slate-300 border border-surface-border transition-colors"
            title="Inspect latest retrieval & adaptive trace"
          >
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>Inspect Evidence</span>
            {inspectedResponse.citations.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-indigo-950 text-indigo-300 text-[10px] font-mono border border-indigo-800/60">
                {inspectedResponse.citations.length} Citations
              </span>
            )}
          </Link>
        )}

        {/* Backend Status Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-card border border-surface-border text-xs">
          <StatusIndicator
            status={health?.status || 'degraded'}
            label={health?.status === 'healthy' ? 'API Online' : health?.status || 'Degraded'}
            size="sm"
          />
          <button
            onClick={() => fetchHealth()}
            disabled={isLoading}
            className="text-slate-400 hover:text-slate-200 transition-colors p-0.5"
            title="Refresh system health"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Tagline Pill */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-950/40 border border-indigo-800/40 text-[11px] text-indigo-300 font-medium">
          <Sparkles className="w-3 h-3 text-indigo-400" />
          <span>Grounded & Adaptive</span>
        </div>
      </div>
    </header>
  );
};
