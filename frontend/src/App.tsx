import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from './pages/LandingPage';
import { WorkspaceLayout } from './pages/WorkspaceLayout';
import { ChatPage } from './pages/ChatPage';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import { RetrievalInspectorPage } from './pages/RetrievalInspectorPage';
import { SystemDashboardPage } from './pages/SystemDashboardPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Landing Page */}
        <Route path="/" element={<LandingPage />} />

        {/* Workspace Shell & Nested Application Pages */}
        <Route path="/app" element={<WorkspaceLayout />}>
          <Route index element={<Navigate to="/app/chat" replace />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="knowledge" element={<KnowledgeBasePage />} />
          <Route path="inspector" element={<RetrievalInspectorPage />} />
          <Route path="dashboard" element={<SystemDashboardPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
