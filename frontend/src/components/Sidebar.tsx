import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  CheckSquare,
  Workflow,
  Bot,
  Users,
  Scale,
  BrainCircuit,
  History,
  FileSpreadsheet,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  modelStatus: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, setCollapsed, modelStatus }) => {
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Task Management', path: '/tasks', icon: CheckSquare },
    { name: 'Create Allocation', path: '/allocate', icon: Workflow },
    { name: 'Agent Workflow', path: '/agents', icon: Bot },
    { name: 'Worker Directory', path: '/workers', icon: Users },
    { name: 'Fairness Analytics', path: '/fairness', icon: Scale },
    { name: 'Model Insights', path: '/model-insights', icon: BrainCircuit },
    { name: 'Allocation History', path: '/history', icon: History },
    { name: 'Reports', path: '/reports', icon: FileSpreadsheet },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 z-30 h-screen transition-all duration-300 ease-in-out bg-white border-r border-[#EAE7F2] flex flex-col justify-between ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div>
        <div className="h-16 flex items-center justify-between px-4 border-b border-[#EAE7F2]">
          {!collapsed ? (
            <div className="flex items-center space-x-2">
              <div className="w-9 h-9 rounded-xl bg-[#F3F0FF] flex items-center justify-center text-[#8B7CF6] shadow-sm">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <span className="font-bold text-lg text-[#29263D] tracking-tight">FairGig AI</span>
                <span className="block text-[10px] text-[#77748C] font-medium leading-none">SDG 8 Task Allocation</span>
              </div>
            </div>
          ) : (
            <div className="mx-auto w-9 h-9 rounded-xl bg-[#F3F0FF] flex items-center justify-center text-[#8B7CF6]">
              <Sparkles className="w-5 h-5" />
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg hover:bg-[#F3F0FF] text-[#77748C] hover:text-[#8B7CF6] transition-colors"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation items */}
        <nav className="p-3 space-y-1 overflow-y-auto max-h-[calc(100vh-180px)]">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 ${
                    isActive
                      ? 'bg-[#F3F0FF] text-[#8B7CF6] font-semibold shadow-xs'
                      : 'text-[#77748C] hover:bg-[#FAF9FE] hover:text-[#29263D]'
                  } ${collapsed ? 'justify-center px-0' : ''}`
                }
                title={collapsed ? item.name : undefined}
              >
                <Icon className={`w-5 h-5 flex-shrink-0`} />
                {!collapsed && <span>{item.name}</span>}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status */}
      <div className="p-3 border-t border-[#EAE7F2] bg-[#FAF9FE]">
        {!collapsed ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#77748C] flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-[#15803D]" /> System:
              </span>
              <span className="text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded-full text-[11px]">Online</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#77748C]">ML Model:</span>
              <span className={`font-medium px-2 py-0.5 rounded-full text-[11px] ${
                modelStatus.includes('Operational') ? 'text-violet-700 bg-violet-50' : 'text-amber-700 bg-amber-50'
              }`}>
                {modelStatus}
              </span>
            </div>
            <div className="text-[10px] text-center text-[#77748C] pt-1">
              Aligned with UN SDG Goal 8
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2" title={`Model: ${modelStatus}`}>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
          </div>
        )}
      </div>
    </aside>
  );
};
