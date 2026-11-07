import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/common/Sidebar';
import { useHealthStore } from '../store/useHealthStore';
import { useKnowledgeStore } from '../store/useKnowledgeStore';

export const WorkspaceLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const { fetchHealth } = useHealthStore();
  const { fetchDocuments } = useKnowledgeStore();

  // Load initial backend health and document list on mount
  useEffect(() => {
    fetchHealth();
    fetchDocuments();

    // Poll health periodically every 45s
    const interval = setInterval(() => {
      fetchHealth();
    }, 45000);

    return () => clearInterval(interval);
  }, [fetchHealth, fetchDocuments]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-slate-100">
      {/* Sidebar */}
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(!collapsed)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative">
        <Outlet context={{ onMobileMenuOpen: () => setMobileOpen(true) }} />
      </div>
    </div>
  );
};
