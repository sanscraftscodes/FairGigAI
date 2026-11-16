import React, { useState, useEffect } from 'react';
import {
  Scale,
  TrendingUp,
  Users,
  ShieldCheck,
  Sliders,
  Play,
  RotateCcw,
  Sparkles,
  BarChart2,
  RefreshCw,
  Info
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { KPICard } from '../components/KPICard';
import { getFairnessSummary, getPolicyComparison, runLambdaSweep } from '../api/client';

export const FairnessPage: React.FC = () => {
  const [summary, setSummary] = useState<any | null>(null);
  const [policyComparison, setPolicyComparison] = useState<any[]>([]);
  const [lambdaVal, setLambdaVal] = useState<number>(0.08);

  const [sweepResults, setSweepResults] = useState<any[]>([]);
  const [sweepInterpretation, setSweepInterpretation] = useState<string | null>(null);
  const [runningSweep, setRunningSweep] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sumRes, compRes] = await Promise.all([
        getFairnessSummary(),
        getPolicyComparison(lambdaVal)
      ]);
      setSummary(sumRes);
      setPolicyComparison(compRes.policies || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [lambdaVal]);

  const handleRunSweep = async () => {
    setRunningSweep(true);
    try {
      const res = await runLambdaSweep();
      setSweepResults(res.sweep_results);
      setSweepInterpretation(res.interpretation);
    } catch (err: any) {
      alert(err.message || 'Failed to run lambda sweep');
    } finally {
      setRunningSweep(false);
    }
  };

  if (loading && !summary) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <RefreshCw className="w-8 h-8 text-[#8B7CF6] animate-spin" />
        <p className="text-sm font-medium text-[#77748C]">Computing fairness equity indicators...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-[#F3F0FF] via-white to-[#D9F3E4]/30 rounded-3xl border border-[#EAE7F2] p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs">
        <div className="space-y-1.5 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-[#EAE7F2] text-xs font-semibold text-[#8B7CF6]">
            <Scale className="w-3.5 h-3.5" />
            <span>Algorithmic Equity & Workload Justice</span>
          </div>
          <h2 className="text-2xl font-bold text-[#29263D]">Fairness Analytics & Policy Auditing</h2>
          <p className="text-xs text-[#77748C] leading-relaxed">
            Quantify exposure equity, prevent gig-worker opportunity starvation, and evaluate trade-offs between proximity, model accuracy, and fairness.
          </p>
        </div>

        <button
          onClick={handleRunSweep}
          disabled={runningSweep}
          className="flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-sm transition-all disabled:opacity-50 self-start md:self-auto"
        >
          {runningSweep ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
          <span>{runningSweep ? 'Simulating Sweep...' : 'Run λ Parameter Sweep'}</span>
        </button>
      </div>

      {/* KPI Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          <KPICard
            title="Jain Fairness"
            value={summary.jain_exposure.toFixed(3)}
            subtitle="1.00 = Perfect equity"
            icon={Scale}
            bgColor="#F3F0FF"
            iconColor="#8B7CF6"
          />
          <KPICard
            title="Gini Exposure"
            value={summary.gini_exposure.toFixed(3)}
            subtitle="0.0 = Minimum disparity"
            icon={TrendingUp}
            bgColor="#F8DDE8"
            iconColor="#EC4899"
          />
          <KPICard
            title="Worker Coverage"
            value={`${(summary.worker_coverage * 100).toFixed(1)}%`}
            subtitle="Share of active workers"
            icon={Users}
            bgColor="#D9F3E4"
            iconColor="#10B981"
          />
          <KPICard
            title="Zero-Exposure Rate"
            value={`${(summary.zero_exposure_rate * 100).toFixed(1)}%`}
            subtitle="Starvation exposure"
            icon={ShieldCheck}
            bgColor="#DCEBFA"
            iconColor="#3B82F6"
          />
          <KPICard
            title="Tasks Allocated"
            value={summary.allocated_tasks.toLocaleString()}
            subtitle="Real allocation records"
            icon={BarChart2}
            bgColor="#FFE7D2"
            iconColor="#F97316"
          />
          <KPICard
            title="Avg Workload"
            value={`${summary.average_workload_hours} hrs`}
            subtitle="7-day working hours"
            icon={Users}
            bgColor="#F3F0FF"
            iconColor="#8B7CF6"
          />
        </div>
      )}

      {/* Charts: Exposure & Workload Distributions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Workload Distribution Histogram */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-base text-[#29263D]">Worker Workload Distribution</h3>
              <p className="text-xs text-[#77748C]">Histogram of workers grouped by recent 7-day working hours</p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#D9F3E4] text-emerald-800 font-semibold">
              Burnout Risk Check
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summary?.workload_distribution || []} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="range" tick={{ fontSize: 11, fill: '#77748C' }} />
                <YAxis tick={{ fontSize: 11, fill: '#77748C' }} />
                <Tooltip />
                <Bar dataKey="count" fill="#8B7CF6" radius={[6, 6, 0, 0]} name="Worker Count" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Task Exposure Distribution */}
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-base text-[#29263D]">Task Allocation Concentration</h3>
              <p className="text-xs text-[#77748C]">Top workers with highest assigned task counts</p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#F3F0FF] text-[#8B7CF6] font-semibold">
              Exposure Tally
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summary?.distribution_exposure || []} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="worker_id" tick={{ fontSize: 11, fill: '#77748C' }} />
                <YAxis tick={{ fontSize: 11, fill: '#77748C' }} />
                <Tooltip />
                <Bar dataKey="tasks_allocated" fill="#EC4899" radius={[6, 6, 0, 0]} name="Tasks Assigned" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Policy Comparison Section */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="font-bold text-base text-[#29263D]">Comparative Policy Audit</h3>
            <p className="text-xs text-[#77748C]">
              Empirical simulation comparing Nearest Eligible (pure distance), ML-Only (greedy probability), and WAFR.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-[#77748C] font-semibold">λ Parameter:</span>
            <input
              type="number"
              step="0.02"
              min="0.0"
              max="0.4"
              value={lambdaVal}
              onChange={(e) => setLambdaVal(parseFloat(e.target.value) || 0.08)}
              className="w-20 px-2.5 py-1 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] font-mono text-center"
            />
          </div>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-[#EAE7F2]">
          <table className="w-full text-xs text-left">
            <thead className="bg-[#FAF9FE] border-b border-[#EAE7F2] text-[#77748C]">
              <tr>
                <th className="py-3 px-4 font-semibold">Allocation Policy</th>
                <th className="py-3 px-4 font-semibold">Mean Distance</th>
                <th className="py-3 px-4 font-semibold">Pred. Success</th>
                <th className="py-3 px-4 font-semibold">Efficiency</th>
                <th className="py-3 px-4 font-semibold">Jain Fairness</th>
                <th className="py-3 px-4 font-semibold">Gini Disparity</th>
                <th className="py-3 px-4 font-semibold">Coverage</th>
                <th className="py-3 px-4 font-semibold">Zero Exposure</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EAE7F2]">
              {policyComparison.map((p, idx) => (
                <tr key={idx} className="hover:bg-[#FAF9FE]">
                  <td className="py-3 px-4 font-bold text-[#29263D] flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      p.policy.includes('WAFR') ? 'bg-[#8B7CF6]' : (p.policy.includes('ML') ? 'bg-pink-400' : 'bg-blue-400')
                    }`}></span>
                    {p.policy}
                  </td>
                  <td className="py-3 px-4 text-[#77748C]">{p.mean_distance_km} km</td>
                  <td className="py-3 px-4 font-bold text-emerald-700">{(p.mean_predicted_success * 100).toFixed(1)}%</td>
                  <td className="py-3 px-4 text-[#77748C]">{p.efficiency_avg?.toFixed(3)}</td>
                  <td className="py-3 px-4 font-bold text-[#8B7CF6]">{p.jain_exposure.toFixed(3)}</td>
                  <td className="py-3 px-4 text-[#77748C]">{p.gini_exposure.toFixed(3)}</td>
                  <td className="py-3 px-4 font-semibold text-emerald-800">{(p.worker_coverage * 100).toFixed(1)}%</td>
                  <td className="py-3 px-4 text-rose-700 font-semibold">{(p.zero_exposure_rate * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Lambda Sweep Results Chart */}
      {sweepResults.length > 0 && (
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-base text-[#29263D]">Fairness Parameter (λ) Sweep Trade-off Curve</h3>
              <p className="text-xs text-[#77748C]">
                Evaluating Jain fairness index and Gini exposure across varying λ values.
              </p>
            </div>
            <span className="text-xs px-3 py-1 rounded-full bg-violet-50 text-violet-700 font-semibold border border-violet-100">
              Live Engine Sweep
            </span>
          </div>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sweepResults} margin={{ top: 10, right: 30, left: -10, bottom: 20 }}>
                <XAxis dataKey="lambda_val" tick={{ fontSize: 11, fill: '#77748C' }} name="Lambda" />
                <YAxis tick={{ fontSize: 11, fill: '#77748C' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="jain_exposure" stroke="#8B7CF6" strokeWidth={2.5} name="Jain Fairness" />
                <Line type="monotone" dataKey="gini_exposure" stroke="#EC4899" strokeWidth={2} name="Gini Exposure" />
                <Line type="monotone" dataKey="worker_coverage" stroke="#10B981" strokeWidth={2} name="Worker Coverage" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {sweepInterpretation && (
            <div className="p-4 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] text-xs text-[#77748C] leading-relaxed flex items-start gap-2.5">
              <Info className="w-4 h-4 text-[#8B7CF6] flex-shrink-0 mt-0.5" />
              <span>{sweepInterpretation}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
