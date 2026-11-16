import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  CheckSquare,
  UserCheck,
  Award,
  TrendingUp,
  Scale,
  PlusCircle,
  Play,
  ArrowRight,
  ExternalLink,
  Layers,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { KPICard } from '../components/KPICard';
import { getDashboardSummary } from '../api/client';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getDashboardSummary();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard summary');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const DONUT_COLORS = ['#8B7CF6', '#F8DDE8', '#D9F3E4', '#DCEBFA', '#FFE7D2', '#C4B5FD'];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <RefreshCw className="w-8 h-8 text-[#8B7CF6] animate-spin" />
        <p className="text-sm font-medium text-[#77748C]">Loading FairGig AI Dashboard...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center my-6">
        <p className="text-red-700 font-semibold mb-2">Error connecting to FairGig backend</p>
        <p className="text-xs text-red-600 mb-4">{error}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-[#8B7CF6] text-white text-xs font-semibold rounded-xl hover:bg-[#7A6AE6]"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const { kpis, charts } = data;

  return (
    <div className="space-y-6 pb-12">
      {/* 5.1 Welcome Section */}
      <div className="bg-gradient-to-r from-[#F3F0FF] via-[#FAF9FE] to-[#F8DDE8]/40 border border-[#EAE7F2] rounded-3xl p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xs">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/80 border border-[#EAE7F2] text-xs font-medium text-[#8B7CF6]">
            <Sparkles className="w-3.5 h-3.5" />
            <span>UN SDG 8: Decent Work & Economic Growth</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#29263D] tracking-tight">
            Welcome to FairGig AI
          </h2>
          <p className="text-xs sm:text-sm text-[#77748C] leading-relaxed">
            Intelligent task allocation powered by worker suitability, dual-model ML predictions, and fairness-aware WAFR optimization.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => navigate('/tasks?create=true')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-white border border-[#EAE7F2] hover:border-[#8B7CF6] text-[#29263D] font-semibold text-xs shadow-xs hover:shadow-md transition-all"
          >
            <PlusCircle className="w-4 h-4 text-[#8B7CF6]" />
            <span>+ Create Task</span>
          </button>
          <button
            onClick={() => navigate('/allocate')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-sm hover:shadow-md transition-all"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Run Allocation</span>
          </button>
        </div>
      </div>

      {/* 5.2 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <KPICard
          title="Total Workers"
          value={kpis.total_workers.toLocaleString()}
          subtitle="Registered gig workers"
          icon={Users}
          bgColor="#F3F0FF"
          iconColor="#8B7CF6"
        />
        <KPICard
          title="Total Tasks"
          value={kpis.total_tasks.toLocaleString()}
          subtitle="Catalog task volume"
          icon={CheckSquare}
          bgColor="#DCEBFA"
          iconColor="#3B82F6"
        />
        <KPICard
          title="Available Candidates"
          value={kpis.available_workers.toLocaleString()}
          subtitle="Active & ready now"
          icon={UserCheck}
          bgColor="#D9F3E4"
          iconColor="#10B981"
        />
        <KPICard
          title="Tasks Allocated"
          value={kpis.tasks_allocated.toLocaleString()}
          subtitle="Assignments confirmed"
          icon={Award}
          bgColor="#FFE7D2"
          iconColor="#F97316"
        />
        <KPICard
          title="Avg Pred. Success"
          value={`${(kpis.avg_predicted_success * 100).toFixed(1)}%`}
          subtitle="Dual-model likelihood"
          icon={TrendingUp}
          bgColor="#F8DDE8"
          iconColor="#EC4899"
        />
        <KPICard
          title="Jain Fairness"
          value={kpis.jain_fairness.toFixed(3)}
          subtitle="Exposure equity index"
          icon={Scale}
          bgColor="#F3F0FF"
          iconColor="#8B7CF6"
        />
      </div>

      {/* 5.3 Dashboard Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart A — Allocation Distribution */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-base text-[#29263D]">Task Allocation Distribution</h3>
              <p className="text-xs text-[#77748C]">Breakdown of tasks across delivery & service categories</p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#F3F0FF] text-[#8B7CF6] font-medium">
              Donut Chart
            </span>
          </div>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={charts.allocation_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {charts.allocation_distribution.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={DONUT_COLORS[index % DONUT_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart B — Worker Workload Distribution */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-base text-[#29263D]">Worker Workload Distribution</h3>
              <p className="text-xs text-[#77748C]">Recent 7-day working hours for sample workers</p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#D9F3E4] text-emerald-800 font-medium">
              Workload Monitoring
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.worker_workload} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="worker_id" tick={{ fontSize: 11, fill: '#77748C' }} />
                <YAxis tick={{ fontSize: 11, fill: '#77748C' }} />
                <Tooltip />
                <Bar dataKey="working_hours_7d" fill="#8B7CF6" radius={[8, 8, 0, 0]} name="7d Hours" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Chart C & D: Policy Comparison and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart C — Policy Comparison */}
        <div className="lg:col-span-2 bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-base text-[#29263D]">Allocation Policy Comparison</h3>
              <p className="text-xs text-[#77748C]">
                Real simulation outcomes comparing Nearest Eligible vs ML-Only vs WAFR (λ=0.08)
              </p>
            </div>
            <button
              onClick={() => navigate('/fairness')}
              className="text-xs text-[#8B7CF6] font-semibold hover:underline flex items-center gap-1"
            >
              <span>Fairness Lab</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-[#EAE7F2] text-[#77748C]">
                  <th className="py-2.5 px-3">Policy</th>
                  <th className="py-2.5 px-3">Avg Distance</th>
                  <th className="py-2.5 px-3">Pred. Success</th>
                  <th className="py-2.5 px-3">Jain Fairness</th>
                  <th className="py-2.5 px-3">Gini Exposure</th>
                  <th className="py-2.5 px-3">Worker Coverage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE7F2]">
                {charts.policy_comparison && charts.policy_comparison.map((pol: any, idx: number) => (
                  <tr key={idx} className="hover:bg-[#FAF9FE] transition-colors">
                    <td className="py-3 px-3 font-semibold text-[#29263D] flex items-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full ${
                        pol.policy.includes('WAFR') ? 'bg-[#8B7CF6]' : (pol.policy.includes('ML') ? 'bg-pink-400' : 'bg-blue-400')
                      }`}></span>
                      {pol.policy}
                    </td>
                    <td className="py-3 px-3 text-[#77748C]">{pol.mean_distance_km} km</td>
                    <td className="py-3 px-3 font-medium text-[#29263D]">{(pol.mean_predicted_success * 100).toFixed(1)}%</td>
                    <td className="py-3 px-3 font-bold text-[#8B7CF6]">{pol.jain_exposure.toFixed(3)}</td>
                    <td className="py-3 px-3 text-[#77748C]">{pol.gini_exposure.toFixed(3)}</td>
                    <td className="py-3 px-3 text-emerald-700 font-medium">{(pol.worker_coverage * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Chart D — Recent Allocation Activity */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-bold text-base text-[#29263D]">Recent Activity</h3>
                <p className="text-xs text-[#77748C]">Latest confirmed task assignments</p>
              </div>
              <button
                onClick={() => navigate('/history')}
                className="text-xs text-[#8B7CF6] font-semibold hover:underline"
              >
                View All
              </button>
            </div>

            <div className="space-y-3">
              {charts.recent_activity && charts.recent_activity.map((item: any) => (
                <div key={item.allocation_id} className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] hover:border-[#8B7CF6] transition-all text-xs">
                  <div className="flex items-center justify-between font-semibold text-[#29263D]">
                    <span>Task {item.task_id}</span>
                    <span className="text-[#8B7CF6] bg-[#F3F0FF] px-2 py-0.5 rounded-full text-[10px]">{item.policy}</span>
                  </div>
                  <div className="flex items-center justify-between text-[#77748C] mt-1.5 text-[11px]">
                    <span>Worker: <strong className="text-[#29263D]">{item.worker_id}</strong></span>
                    <span>WAFR: <strong className="text-[#29263D]">{item.wafr_score}</strong></span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Actions Footer */}
          <div className="pt-4 border-t border-[#EAE7F2] mt-4 flex items-center justify-between">
            <button
              onClick={() => navigate('/agents')}
              className="text-xs text-[#77748C] hover:text-[#8B7CF6] font-medium flex items-center gap-1"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Inspect Agents</span>
            </button>
            <button
              onClick={() => navigate('/model-insights')}
              className="text-xs text-[#77748C] hover:text-[#8B7CF6] font-medium flex items-center gap-1"
            >
              <span>Model Insights</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
