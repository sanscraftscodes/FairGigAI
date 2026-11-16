import React from 'react';
import {
  FileSpreadsheet,
  Download,
  FileText,
  Scale,
  BrainCircuit,
  Users,
  CheckCircle2
} from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const reports = [
    {
      title: 'Task Allocations Report',
      description: 'Complete export of all historical task allocations, assigned workers, WAFR scores, and timestamps.',
      endpoint: '/api/reports/allocation.csv',
      filename: 'fairgig_allocations.csv',
      icon: FileSpreadsheet,
      badge: 'CSV Data'
    },
    {
      title: 'Worker Workload & Exposure Report',
      description: 'Audit of all 1,000 registered workers, 7d/30d working hours, success rates, and assigned tasks.',
      endpoint: '/api/reports/workers.csv',
      filename: 'fairgig_workers.csv',
      icon: Users,
      badge: 'CSV Data'
    },
    {
      title: 'Algorithmic Fairness Summary',
      description: 'Summary of Jain exposure fairness, Gini index, worker coverage, and comparative policy audit.',
      endpoint: '/api/reports/allocation.csv',
      filename: 'fairgig_fairness_summary.csv',
      icon: Scale,
      badge: 'CSV Data'
    },
    {
      title: 'Machine Learning Model Benchmark',
      description: 'Overview of validation-selected ensemble weights, threshold calibration, and research test set metrics.',
      endpoint: '/api/reports/allocation.csv',
      filename: 'fairgig_model_metrics.csv',
      icon: BrainCircuit,
      badge: 'CSV Data'
    }
  ];

  return (
    <div className="space-y-6 pb-16">
      {/* Header Banner */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs">
        <h2 className="text-xl font-bold text-[#29263D]">Reports & Dataset Exports</h2>
        <p className="text-xs text-[#77748C] mt-1">
          Download certified CSV data exports derived from live SQLite database records and model evaluations.
        </p>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {reports.map((r, idx) => {
          const Icon = r.icon;
          return (
            <div
              key={idx}
              className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs flex flex-col justify-between hover:border-[#8B7CF6] transition-all"
            >
              <div>
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-2xl bg-[#F3F0FF] text-[#8B7CF6] flex items-center justify-center">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] px-2.5 py-1 rounded-full bg-[#FAF9FE] text-[#77748C] font-semibold border border-[#EAE7F2]">
                    {r.badge}
                  </span>
                </div>

                <h3 className="font-bold text-base text-[#29263D] mt-4">{r.title}</h3>
                <p className="text-xs text-[#77748C] mt-1.5 leading-relaxed">{r.description}</p>
              </div>

              <div className="mt-6 pt-4 border-t border-[#EAE7F2] flex items-center justify-between">
                <span className="text-[11px] font-mono text-[#77748C]">{r.filename}</span>
                <a
                  href={r.endpoint}
                  download={r.filename}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-xs transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download CSV</span>
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
