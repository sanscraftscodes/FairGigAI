import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Bell,
  HelpCircle,
  Search,
  User,
  ExternalLink,
  Info,
  CheckCircle2,
  X
} from 'lucide-react';

interface HeaderProps {
  collapsed: boolean;
  onOpenHelp: () => void;
}

export const Header: React.FC<HeaderProps> = ({ collapsed, onOpenHelp }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  // Derive title from pathname
  const routeTitles: Record<string, string> = {
    '/dashboard': 'Overview Dashboard',
    '/tasks': 'Task Management',
    '/allocate': 'Create Allocation Workflow',
    '/agents': 'Multi-Agent Workflow Architecture',
    '/workers': 'Worker Directory',
    '/fairness': 'Fairness & Equity Analytics',
    '/model-insights': 'ML Model Insights & Calibration',
    '/history': 'Allocation History',
    '/reports': 'Reports & Data Export',
    '/settings': 'System Settings'
  };

  const currentTitle = routeTitles[location.pathname] || 'FairGig AI';

  const notifications = [
    { id: 1, title: 'Database Connected', message: 'SQLite fairgig.db active with 1,000 workers & 3,000 tasks.', time: 'Just now', type: 'success' },
    { id: 2, title: 'ML Ensemble Loaded', message: 'HistGradientBoosting + CatBoost validated (threshold: 0.155).', time: '5m ago', type: 'info' },
    { id: 3, title: 'SDG 8 Alignment Active', message: 'Workload pressure balancing and opportunity credits enabled.', time: '10m ago', type: 'info' }
  ];

  return (
    <header
      className={`fixed top-0 right-0 z-20 h-16 bg-white/90 backdrop-blur-md border-b border-[#EAE7F2] transition-all duration-300 flex items-center justify-between px-6 ${
        collapsed ? 'left-20' : 'left-64'
      }`}
    >
      {/* Title & Breadcrumbs */}
      <div>
        <div className="flex items-center space-x-2 text-xs text-[#77748C]">
          <span>FairGig AI</span>
          <span>/</span>
          <span className="text-[#8B7CF6] font-medium capitalize">
            {location.pathname.replace('/', '') || 'dashboard'}
          </span>
        </div>
        <h1 className="text-lg font-bold text-[#29263D] leading-tight">{currentTitle}</h1>
      </div>

      {/* Action Bar */}
      <div className="flex items-center space-x-3">
        {/* Quick Help Button */}
        <button
          onClick={onOpenHelp}
          className="p-2 rounded-xl text-[#77748C] hover:text-[#8B7CF6] hover:bg-[#F3F0FF] transition-colors relative"
          title="Project Documentation & Guide"
        >
          <HelpCircle className="w-5 h-5" />
        </button>

        {/* Notifications Icon & Popover */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-xl text-[#77748C] hover:text-[#8B7CF6] hover:bg-[#F3F0FF] transition-colors relative"
            title="System Notifications"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#8B7CF6]"></span>
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-xl border border-[#EAE7F2] p-4 z-50">
              <div className="flex items-center justify-between pb-3 border-b border-[#EAE7F2]">
                <h4 className="font-semibold text-sm text-[#29263D]">Application Notifications</h4>
                <button
                  onClick={() => setShowNotifications(false)}
                  className="text-[#77748C] hover:text-[#29263D]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="py-2 space-y-2 max-h-60 overflow-y-auto">
                {notifications.map((n) => (
                  <div key={n.id} className="p-2.5 rounded-xl bg-[#FAF9FE] hover:bg-[#F3F0FF] transition-colors text-xs">
                    <div className="flex items-center justify-between font-medium text-[#29263D]">
                      <span>{n.title}</span>
                      <span className="text-[10px] text-[#77748C]">{n.time}</span>
                    </div>
                    <p className="text-[#77748C] mt-0.5 leading-relaxed">{n.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Profile Menu */}
        <div className="relative">
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center space-x-2 pl-2 pr-3 py-1.5 rounded-xl border border-[#EAE7F2] hover:border-[#8B7CF6] transition-colors"
          >
            <div className="w-7 h-7 rounded-lg bg-[#F8DDE8] flex items-center justify-center text-[#29263D] font-bold text-xs">
              FG
            </div>
            <span className="text-xs font-semibold text-[#29263D]">Administrator</span>
          </button>

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-[#EAE7F2] p-2 z-50">
              <div className="px-3 py-2 border-b border-[#EAE7F2]">
                <p className="text-xs font-bold text-[#29263D]">FairGig Administrator</p>
                <p className="text-[11px] text-[#77748C]">SDG 8 Task Allocation Platform</p>
              </div>
              <div className="py-1">
                <button
                  onClick={() => { setShowProfileMenu(false); navigate('/settings'); }}
                  className="w-full text-left px-3 py-2 text-xs text-[#29263D] hover:bg-[#F3F0FF] rounded-lg transition-colors"
                >
                  System Settings
                </button>
                <button
                  onClick={() => { setShowProfileMenu(false); onOpenHelp(); }}
                  className="w-full text-left px-3 py-2 text-xs text-[#29263D] hover:bg-[#F3F0FF] rounded-lg transition-colors flex items-center justify-between"
                >
                  <span>About FairGig AI</span>
                  <ExternalLink className="w-3.5 h-3.5 text-[#77748C]" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
