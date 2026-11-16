import React, { useState, useEffect } from 'react';
import {
  History as HistoryIcon,
  Search,
  Filter,
  Eye,
  Download,
  Calendar,
  X,
  ShieldCheck,
  Award,
  Sparkles
} from 'lucide-react';
import { getAllocationHistory, getHistoryDetail } from '../api/client';

export const HistoryPage: React.FC = () => {
  const [allocations, setAllocations] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [policy, setPolicy] = useState('all');
  const [status, setStatus] = useState('all');
  const [workerId, setWorkerId] = useState('');
  const [taskId, setTaskId] = useState('');
  const [loading, setLoading] = useState(true);

  // Detail Modal
  const [selectedAllocId, setSelectedAllocId] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const res = await getAllocationHistory({
        policy: policy,
        status: status,
        worker_id: workerId,
        task_id: taskId,
        page: page,
        limit: 15
      });
      setAllocations(res.allocations);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [page, policy, status]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadHistory();
  };

  const handleOpenDetail = async (allocId: string) => {
    setSelectedAllocId(allocId);
    setDetailLoading(true);
    try {
      const res = await getHistoryDetail(allocId);
      setDetailData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#29263D]">Confirmed Allocation History</h2>
          <p className="text-xs text-[#77748C]">
            Audit historical task allocations, candidate rankings, and explainable justifications.
          </p>
        </div>
        <a
          href="/api/reports/allocation.csv"
          download="fairgig_allocations.csv"
          className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-sm transition-all self-start sm:self-auto"
        >
          <Download className="w-4 h-4" />
          <span>Export All CSV</span>
        </a>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3 flex-1">
          <div className="relative min-w-[180px]">
            <Search className="w-4 h-4 text-[#77748C] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search Task ID..."
              value={taskId}
              onChange={(e) => setTaskId(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-xs focus:outline-none focus:border-[#8B7CF6]"
            />
          </div>
          <div className="relative min-w-[180px]">
            <Search className="w-4 h-4 text-[#77748C] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search Worker ID..."
              value={workerId}
              onChange={(e) => setWorkerId(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-xs focus:outline-none focus:border-[#8B7CF6]"
            />
          </div>
          <button
            type="submit"
            className="px-3.5 py-2 bg-[#F3F0FF] text-[#8B7CF6] rounded-xl text-xs font-semibold hover:bg-[#8B7CF6] hover:text-white transition-all"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-3 text-xs">
          <select
            value={policy}
            onChange={(e) => { setPolicy(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
          >
            <option value="all">All Policies</option>
            <option value="WAFR">WAFR</option>
            <option value="ML-Only">ML-Only</option>
            <option value="Nearest Eligible">Nearest Eligible</option>
          </select>

          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
          >
            <option value="all">All Statuses</option>
            <option value="confirmed">Confirmed</option>
            <option value="draft">Draft</option>
          </select>
        </div>
      </div>

      {/* History Records Table */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-[#FAF9FE] border-b border-[#EAE7F2] text-[#77748C]">
              <tr>
                <th className="py-3 px-4 font-semibold">Allocation ID</th>
                <th className="py-3 px-4 font-semibold">Task ID</th>
                <th className="py-3 px-4 font-semibold">Assigned Worker</th>
                <th className="py-3 px-4 font-semibold">Policy</th>
                <th className="py-3 px-4 font-semibold">P(Success)</th>
                <th className="py-3 px-4 font-semibold">WAFR Score</th>
                <th className="py-3 px-4 font-semibold">Lambda (λ)</th>
                <th className="py-3 px-4 font-semibold">Timestamp</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EAE7F2]">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-[#77748C]">
                    Loading allocation history...
                  </td>
                </tr>
              ) : allocations.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-[#77748C]">
                    No allocation records found.
                  </td>
                </tr>
              ) : (
                allocations.map((a) => (
                  <tr key={a.allocation_id} className="hover:bg-[#FAF9FE] transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-[#8B7CF6]">
                      {a.allocation_id}
                    </td>
                    <td className="py-3 px-4 font-semibold text-[#29263D]">
                      {a.task_id}
                    </td>
                    <td className="py-3 px-4 font-semibold text-[#29263D]">
                      {a.worker_id}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full bg-[#F3F0FF] text-[#8B7CF6] font-semibold text-[10px]">
                        {a.policy}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-bold text-emerald-700">
                      {(a.predicted_success * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 font-semibold text-[#29263D]">
                      {a.wafr_score.toFixed(4)}
                    </td>
                    <td className="py-3 px-4 text-[#77748C] font-mono">
                      λ = {a.lambda_val}
                    </td>
                    <td className="py-3 px-4 text-[#77748C]">
                      {new Date(a.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenDetail(a.allocation_id)}
                        className="p-1.5 rounded-lg hover:bg-[#F3F0FF] text-[#77748C] hover:text-[#8B7CF6] transition-colors"
                        title="View Full Audit Record"
                      >
                        <Eye className="w-4 h-4 inline" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-4 border-t border-[#EAE7F2] bg-[#FAF9FE] flex items-center justify-between text-xs text-[#77748C]">
          <span>Showing {allocations.length} of {total} allocations</span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-xl border border-[#EAE7F2] bg-white disabled:opacity-40 hover:bg-[#FAF9FE]"
            >
              Previous
            </button>
            <span className="font-semibold text-[#29263D]">Page {page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={allocations.length < 15}
              className="px-3 py-1.5 rounded-xl border border-[#EAE7F2] bg-white disabled:opacity-40 hover:bg-[#FAF9FE]"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Allocation Detail Modal */}
      {selectedAllocId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl border border-[#EAE7F2] shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto">
            <div className="p-6 border-b border-[#EAE7F2] flex items-center justify-between sticky top-0 bg-white z-10">
              <div>
                <span className="text-[10px] uppercase font-bold text-[#77748C]">Audit Record</span>
                <h3 className="font-bold text-base text-[#29263D]">{selectedAllocId}</h3>
              </div>
              <button
                onClick={() => setSelectedAllocId(null)}
                className="p-2 rounded-xl text-[#77748C] hover:bg-[#F3F0FF]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {detailLoading || !detailData ? (
              <p className="text-xs text-[#77748C] text-center py-12">Loading audit details...</p>
            ) : (
              <div className="p-6 space-y-5 text-xs">
                {/* Summary Card */}
                <div className="p-5 rounded-2xl bg-gradient-to-r from-violet-50 to-[#FAF9FE] border border-violet-100 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-[#77748C] uppercase font-bold block">Assigned Worker</span>
                      <strong className="text-xl font-extrabold text-[#29263D]">{detailData.allocation.worker_id}</strong>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-[#77748C] uppercase font-bold block">WAFR Score</span>
                      <strong className="text-xl font-extrabold text-[#8B7CF6]">{detailData.allocation.wafr_score}</strong>
                    </div>
                  </div>

                  <p className="text-xs text-[#29263D] leading-relaxed pt-2 border-t border-violet-100">
                    {detailData.allocation.explanation}
                  </p>
                </div>

                {/* Score Decomposition */}
                <div className="grid grid-cols-4 gap-3 text-center">
                  <div className="p-3 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] block uppercase font-bold">P(Success)</span>
                    <strong className="text-emerald-700 font-bold text-sm">
                      {(detailData.allocation.predicted_success * 100).toFixed(1)}%
                    </strong>
                  </div>
                  <div className="p-3 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] block uppercase font-bold">Efficiency</span>
                    <strong className="text-[#29263D] font-bold text-sm">
                      {detailData.allocation.efficiency}
                    </strong>
                  </div>
                  <div className="p-3 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] block uppercase font-bold">Opportunity</span>
                    <strong className="text-[#8B7CF6] font-bold text-sm">
                      {detailData.allocation.opportunity_credit}
                    </strong>
                  </div>
                  <div className="p-3 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] block uppercase font-bold">Workload Press.</span>
                    <strong className="text-pink-700 font-bold text-sm">
                      {detailData.allocation.workload_pressure}
                    </strong>
                  </div>
                </div>

                {/* Top Candidates Ranking */}
                {detailData.rankings && detailData.rankings.length > 0 && (
                  <div>
                    <h4 className="font-bold text-xs text-[#29263D] mb-2">Evaluated Candidate Rankings</h4>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto">
                      {detailData.rankings.map((c: any, idx: number) => (
                        <div
                          key={idx}
                          className={`p-2.5 rounded-xl border text-xs flex items-center justify-between ${
                            c.rank === 1
                              ? 'bg-violet-50/70 border-violet-200 font-semibold'
                              : 'bg-white border-[#EAE7F2]'
                          }`}
                        >
                          <span className="font-mono text-[#8B7CF6]">#{c.rank || idx + 1} {c.worker_id}</span>
                          <div className="space-x-3 text-[#77748C]">
                            {c.predicted_success !== undefined && (
                              <span>P(succ): <strong className="text-[#29263D]">{(c.predicted_success * 100).toFixed(0)}%</strong></span>
                            )}
                            {c.wafr_score !== undefined && (
                              <span>WAFR: <strong className="text-[#8B7CF6]">{c.wafr_score}</strong></span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="p-4 border-t border-[#EAE7F2] bg-[#FAF9FE] rounded-b-3xl flex justify-end">
              <button
                onClick={() => setSelectedAllocId(null)}
                className="px-4 py-2 rounded-xl bg-[#8B7CF6] text-white font-semibold text-xs hover:bg-[#7A6AE6]"
              >
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
