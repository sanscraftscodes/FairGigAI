import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { HelpModal } from './components/HelpModal';

// Pages
import { DashboardPage } from './pages/DashboardPage';
import { TasksPage } from './pages/TasksPage';
import { AllocatePage } from './pages/AllocatePage';
import { AgentsPage } from './pages/AgentsPage';
import { WorkersPage } from './pages/WorkersPage';
import { FairnessPage } from './pages/FairnessPage';
import { ModelInsightsPage } from './pages/ModelInsightsPage';
import { HistoryPage } from './pages/HistoryPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

import { getModelStatus } from './api/client';

export const App: React.FC = () => {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [isHelpOpen, setIsHelpOpen] = useState<boolean>(false);
  const [modelStatus, setModelStatus] = useState<string>('Checking...');

  useEffect(() => {
    localStorage.removeItem('fairgig_gemini_api_key');
    getModelStatus()
      .then((res) => {
        setModelStatus(res.environment_status || 'Operational');
      })
      .catch(() => {
        setModelStatus('Backend Offline');
      });
  }, []);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#FAF9FE] text-[#29263D] flex flex-col">
        {/* Persistent Collapsible Sidebar */}
        <Sidebar
          collapsed={collapsed}
          setCollapsed={setCollapsed}
          modelStatus={modelStatus}
        />

        {/* Global Header */}
        <Header
          collapsed={collapsed}
          onOpenHelp={() => setIsHelpOpen(true)}
        />

        {/* Main Application Content Area */}
        <main
          className={`flex-1 transition-all duration-300 pt-20 px-6 sm:px-8 ${
            collapsed ? 'ml-20' : 'ml-64'
          }`}
        >
          <div className="max-w-7xl mx-auto">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/tasks" element={<TasksPage />} />
              <Route path="/allocate" element={<AllocatePage />} />
              <Route path="/agents" element={<AgentsPage />} />
              <Route path="/workers" element={<WorkersPage />} />
              <Route path="/fairness" element={<FairnessPage />} />
              <Route path="/model-insights" element={<ModelInsightsPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </div>
        </main>

        {/* Help / Guide Documentation Modal */}
        <HelpModal
          isOpen={isHelpOpen}
          onClose={() => setIsHelpOpen(false)}
        />
      </div>
    </BrowserRouter>
  );
};

export default App;
