import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  MessageSquare,
  FolderGit2,
  SearchCode,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  ShieldCheck,
} from 'lucide-react';
import { useKnowledgeStore } from '../../store/useKnowledgeStore';
import { useHealthStore } from '../../store/useHealthStore';
import { StatusIndicator } from './StatusIndicator';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onToggle,
  mobileOpen = false,
  onMobileClose,
}) => {
  const { total: documentCount } = useKnowledgeStore();
  const { health } = useHealthStore();

  const navItems = [
    {
      to: '/app/chat',
      label: 'AI Chat',
      icon: MessageSquare,
      badge: null,
    },
    {
      to: '/app/knowledge',
      label: 'Knowledge Base',
      icon: FolderGit2,
      badge: documentCount > 0 ? documentCount : null,
    },
    {
      to: '/app/inspector',
      label: 'Retrieval Inspector',
      icon: SearchCode,
      badge: 'Phase 4',
    },
    {
      to: '/app/dashboard',
      label: 'System Health',
      icon: Activity,
      badge: null,
    },
    {
      to: '/app/settings',
      label: 'Settings',
      icon: Settings,
      badge: null,
    },
  ];

  const sidebarContent = (
    <div className="flex flex-col h-full bg-surface-muted/95 border-r border-surface-border backdrop-blur-md select-none">
      {/* Brand Header */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-surface-border">
        <Link
          to="/"
          className={`flex items-center gap-3 transition-opacity ${
            collapsed ? 'justify-center w-full' : ''
          }`}
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-700 flex items-center justify-center shadow-glow-primary shrink-0">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-semibold text-base tracking-tight text-white flex items-center gap-1.5">
                VeriWeave
                <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-indigo-950 text-indigo-400 border border-indigo-800/60">
                  v0.4
                </span>
              </span>
              <span className="text-[11px] text-slate-400 truncate max-w-[140px]">
                Adaptive RAG Engine
              </span>
            </div>
          )}
        </Link>
        {!collapsed && onToggle && (
          <button
            onClick={onToggle}
            className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-surface-hover transition-colors hidden md:block"
            title="Collapse sidebar"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => onMobileClose?.()}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-surface-hover/80'
                } ${collapsed ? 'justify-center' : ''}`
              }
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-5 h-5 shrink-0" />
              {!collapsed && (
                <span className="flex-1 truncate">{item.label}</span>
              )}
              {!collapsed && item.badge !== null && (
                <span
                  className={`text-[11px] font-mono px-2 py-0.5 rounded-full font-semibold ${
                    typeof item.badge === 'number'
                      ? 'bg-slate-800 text-slate-300'
                      : 'bg-indigo-950 text-indigo-300 border border-indigo-800/60'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* System Status Footer */}
      <div className="p-3 border-t border-surface-border">
        <Link
          to="/app/dashboard"
          className={`flex items-center gap-3 p-2.5 rounded-xl bg-surface-card/60 border border-surface-border hover:bg-surface-hover/80 transition-colors ${
            collapsed ? 'justify-center' : ''
          }`}
          title={health ? `Status: ${health.status}` : 'Connecting...'}
        >
          <StatusIndicator status={health?.status || 'degraded'} size="sm" />
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-300 truncate">
                  Backend System
                </span>
                <span className="text-[10px] text-slate-500 font-mono capitalize">
                  {health?.status || 'Connecting'}
                </span>
              </div>
              <p className="text-[10px] text-slate-400 truncate">
                {String(health?.components.llm_engine?.details?.model || 'Local Model')}
              </p>
            </div>
          )}
        </Link>

        {/* Return to Landing Page */}
        <Link
          to="/"
          className={`mt-2 flex items-center gap-2 px-3 py-2 text-xs text-slate-400 hover:text-slate-300 hover:bg-surface-hover rounded-lg transition-colors ${
            collapsed ? 'justify-center' : ''
          }`}
          title="Back to Landing Page"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          {!collapsed && <span>Public Overview</span>}
        </Link>
      </div>

      {/* Expand button when collapsed */}
      {collapsed && (
        <div className="p-2 border-t border-surface-border flex justify-center">
          <button
            onClick={onToggle}
            className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-surface-hover transition-colors"
            title="Expand sidebar"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={`hidden md:block shrink-0 transition-all duration-300 ease-in-out ${
          collapsed ? 'w-16' : 'w-64'
        }`}
      >
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onMobileClose}
          />
          <div className="relative w-64 max-w-[80vw] h-full z-10 animate-slide-right">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
