import React, { useState, useEffect } from 'react';
import {
  Users,
  Search,
  Filter,
  UserCheck,
  PlusCircle,
  Eye,
  X,
  TrendingUp,
  Clock,
  Award,
  Layers,
  Sparkles
} from 'lucide-react';
import { getWorkers, getWorkerDetail, createSyntheticWorker } from '../api/client';

export const WorkersPage: React.FC = () => {
  const [workers, setWorkers] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [skill, setSkill] = useState('all');
  const [vehicle, setVehicle] = useState('all');
  const [availability, setAvailability] = useState('all');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('worker_id');
  const [sortOrder, setSortOrder] = useState('asc');
  const [loading, setLoading] = useState(true);

  // Detail panel state
  const [selectedWorkerId, setSelectedWorkerId] = useState<string | null>(null);
  const [workerDetail, setWorkerDetail] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Synthetic demo worker modal
  const [showSyntheticModal, setShowSyntheticModal] = useState(false);
  const [syntheticForm, setSyntheticForm] = useState({
    experience_years: 3.5,
    availability_status: 'available',
    vehicle_type: 'bike',
    vehicle_available: true,
    max_package_weight_kg: 18.0,
    archetype: 'balanced',
    skills: 'driving,navigation,handling'
  });

  const loadWorkers = async () => {
    try {
      setLoading(true);
      const res = await getWorkers({
        skill: skill,
        vehicle_type: vehicle,
        availability: availability,
        search: search,
        sort_by: sortBy,
        sort_order: sortOrder,
        page: page,
        limit: 15
      });
      setWorkers(res.workers);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkers();
  }, [page, skill, vehicle, availability, sortBy, sortOrder]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadWorkers();
  };

  const handleOpenDetail = async (workerId: string) => {
    setSelectedWorkerId(workerId);
    setDetailLoading(true);
    try {
      const res = await getWorkerDetail(workerId);
      setWorkerDetail(res);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreateSynthetic = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createSyntheticWorker(syntheticForm);
      setShowSyntheticModal(false);
      setPage(1);
      loadWorkers();
    } catch (err: any) {
      alert(err.message || 'Error creating synthetic demo worker');
    }
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#29263D]">Worker Directory & Profiles</h2>
          <p className="text-xs text-[#77748C]">
            Inspect gig-worker skills, vehicle availability, recent workload, and exposure history.
          </p>
        </div>
        <button
          onClick={() => setShowSyntheticModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] hover:border-[#8B7CF6] text-[#8B7CF6] font-semibold text-xs transition-all self-start sm:self-auto"
        >
          <Sparkles className="w-4 h-4" />
          <span>+ Add Synthetic Demo Worker</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-[#77748C] absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search workers by ID, archetype, or skill..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-xs focus:outline-none focus:border-[#8B7CF6]"
          />
        </form>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* Skill Filter */}
          <select
            value={skill}
            onChange={(e) => { setSkill(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
          >
            <option value="all">All Skills</option>
            <option value="driving">driving</option>
            <option value="navigation">navigation</option>
            <option value="handling">handling</option>
            <option value="customer_service">customer_service</option>
            <option value="time_management">time_management</option>
            <option value="cold_chain">cold_chain</option>
          </select>

          {/* Vehicle Filter */}
          <select
            value={vehicle}
            onChange={(e) => { setVehicle(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
          >
            <option value="all">All Vehicles</option>
            <option value="bike">Bike</option>
            <option value="scooter">Scooter</option>
            <option value="car">Car</option>
            <option value="van">Van</option>
          </select>

          {/* Availability Filter */}
          <select
            value={availability}
            onChange={(e) => { setAvailability(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
          >
            <option value="all">All Availability</option>
            <option value="available">Available</option>
            <option value="busy">Busy</option>
            <option value="offline">Offline</option>
          </select>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
          >
            <option value="worker_id">Sort by ID</option>
            <option value="working_hours_7d">Sort by Workload (7d)</option>
            <option value="success_rate_30d">Sort by Success Rate</option>
            <option value="total_tasks_allocated">Sort by Tasks Assigned</option>
          </select>
        </div>
      </div>

      {/* Workers Table */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-[#FAF9FE] border-b border-[#EAE7F2] text-[#77748C]">
              <tr>
                <th className="py-3 px-4 font-semibold">Worker ID</th>
                <th className="py-3 px-4 font-semibold">Vehicle</th>
                <th className="py-3 px-4 font-semibold">Availability</th>
                <th className="py-3 px-4 font-semibold">Experience</th>
                <th className="py-3 px-4 font-semibold">Skills</th>
                <th className="py-3 px-4 font-semibold">7d Workload</th>
                <th className="py-3 px-4 font-semibold">30d Success</th>
                <th className="py-3 px-4 font-semibold">Exposure</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EAE7F2]">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-[#77748C]">
                    Loading worker records...
                  </td>
                </tr>
              ) : workers.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-[#77748C]">
                    No workers found matching the filters.
                  </td>
                </tr>
              ) : (
                workers.map((w) => (
                  <tr key={w.worker_id} className="hover:bg-[#FAF9FE] transition-colors">
                    <td className="py-3 px-4 font-bold text-[#8B7CF6] flex items-center gap-1.5">
                      <span>{w.worker_id}</span>
                      {w.is_synthetic && (
                        <span className="text-[9px] bg-pink-100 text-pink-700 px-1.5 py-0.2 rounded-full font-semibold">
                          SYNTH
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-[#29263D] capitalize">
                      {w.vehicle_type}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold capitalize ${
                        w.availability_status === 'available'
                          ? 'bg-emerald-50 text-emerald-700'
                          : w.availability_status === 'busy'
                          ? 'bg-amber-50 text-amber-700'
                          : 'bg-slate-100 text-slate-600'
                      }`}>
                        {w.availability_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[#77748C]">
                      {w.experience_years.toFixed(1)} yrs
                    </td>
                    <td className="py-3 px-4 text-[#77748C]">
                      <span className="truncate max-w-[160px] block font-mono text-[11px]" title={w.skills}>
                        {w.skills}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-medium text-[#29263D]">
                      {w.working_hours_7d.toFixed(1)} hrs
                    </td>
                    <td className="py-3 px-4 font-semibold text-emerald-700">
                      {(w.success_rate_30d * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-[#77748C]">
                      {(w.recent_exposure * 100).toFixed(0)}%
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenDetail(w.worker_id)}
                        className="p-1.5 rounded-lg hover:bg-[#F3F0FF] text-[#77748C] hover:text-[#8B7CF6] transition-colors"
                        title="View Worker Profile"
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
          <span>Showing {workers.length} of {total} workers</span>
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
              disabled={workers.length < 15}
              className="px-3 py-1.5 rounded-xl border border-[#EAE7F2] bg-white disabled:opacity-40 hover:bg-[#FAF9FE]"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Worker Detail Panel */}
      {selectedWorkerId && (
        <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-md bg-white h-full shadow-2xl p-6 overflow-y-auto space-y-6 animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-[#EAE7F2]">
              <div>
                <span className="text-xs text-[#77748C] uppercase tracking-wider font-semibold">Worker Dossier</span>
                <h3 className="text-lg font-bold text-[#29263D]">{selectedWorkerId}</h3>
              </div>
              <button
                onClick={() => setSelectedWorkerId(null)}
                className="p-2 rounded-xl text-[#77748C] hover:bg-[#F3F0FF]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {detailLoading || !workerDetail ? (
              <p className="text-xs text-[#77748C] text-center py-12">Loading worker profile...</p>
            ) : (
              <div className="space-y-5 text-xs">
                {/* Profile Overview */}
                <div className="p-4 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#29263D] text-sm capitalize">
                      Archetype: {workerDetail.worker.archetype}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-semibold capitalize">
                      {workerDetail.worker.availability_status}
                    </span>
                  </div>
                  <p className="text-[11px] text-[#77748C]">
                    Vehicle: <strong>{workerDetail.worker.vehicle_type}</strong> (capacity: {workerDetail.worker.max_package_weight_kg}kg)
                  </p>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-[#77748C] block mb-1">Skills</span>
                    <div className="flex flex-wrap gap-1.5">
                      {workerDetail.worker.skills.split(',').map((s: string) => (
                        <span key={s} className="px-2 py-0.5 bg-white border border-[#EAE7F2] rounded-lg font-mono text-[10px] text-[#8B7CF6]">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Performance stats */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] uppercase font-bold block">Recent 7d Workload</span>
                    <p className="font-bold text-sm text-[#29263D] mt-0.5">{workerDetail.performance_profile.working_hours_7d.toFixed(1)} hrs</p>
                  </div>
                  <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] uppercase font-bold block">30d Success Rate</span>
                    <p className="font-bold text-sm text-emerald-700 mt-0.5">{(workerDetail.performance_profile.success_rate_30d * 100).toFixed(1)}%</p>
                  </div>
                  <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] uppercase font-bold block">Cancellation Rate</span>
                    <p className="font-bold text-sm text-[#29263D] mt-0.5">{(workerDetail.performance_profile.cancellation_rate_30d * 100).toFixed(1)}%</p>
                  </div>
                  <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] uppercase font-bold block">Average Delay</span>
                    <p className="font-bold text-sm text-[#29263D] mt-0.5">{workerDetail.performance_profile.avg_delay_min_30d.toFixed(1)} mins</p>
                  </div>
                </div>

                {/* Task Affinities */}
                <div className="p-4 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] space-y-2">
                  <span className="text-[10px] text-[#77748C] uppercase font-bold block">Category Affinities</span>
                  <div className="grid grid-cols-3 gap-2 text-center text-[11px]">
                    {Object.entries(workerDetail.performance_profile.affinities).map(([cat, val]: any) => (
                      <div key={cat} className="p-1.5 bg-white rounded-xl border border-[#EAE7F2]">
                        <span className="capitalize text-[#77748C] block text-[10px]">{cat}</span>
                        <strong className="text-[#8B7CF6]">{(val * 100).toFixed(0)}%</strong>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Synthetic Worker Modal */}
      {showSyntheticModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl border border-[#EAE7F2] shadow-2xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#EAE7F2]">
              <div>
                <h3 className="font-bold text-base text-[#29263D]">Create Synthetic Demo Worker</h3>
                <p className="text-xs text-[#77748C]">Creates a clearly marked synthetic record for testing allocation edge cases.</p>
              </div>
              <button onClick={() => setShowSyntheticModal(false)} className="p-2 rounded-xl text-[#77748C] hover:bg-[#F3F0FF]">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSynthetic} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-[#29263D] mb-1">Vehicle Type</label>
                  <select
                    value={syntheticForm.vehicle_type}
                    onChange={(e) => setSyntheticForm({ ...syntheticForm, vehicle_type: e.target.value })}
                    className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE]"
                  >
                    <option value="bike">Bike</option>
                    <option value="scooter">Scooter</option>
                    <option value="car">Car</option>
                    <option value="van">Van</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-[#29263D] mb-1">Availability</label>
                  <select
                    value={syntheticForm.availability_status}
                    onChange={(e) => setSyntheticForm({ ...syntheticForm, availability_status: e.target.value })}
                    className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE]"
                  >
                    <option value="available">Available</option>
                    <option value="busy">Busy</option>
                    <option value="offline">Offline</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-[#29263D] mb-1">Experience (Years)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={syntheticForm.experience_years}
                    onChange={(e) => setSyntheticForm({ ...syntheticForm, experience_years: parseFloat(e.target.value) || 0 })}
                    className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE]"
                  />
                </div>
                <div>
                  <label className="block font-medium text-[#29263D] mb-1">Max Capacity (kg)</label>
                  <input
                    type="number"
                    step="1.0"
                    value={syntheticForm.max_package_weight_kg}
                    onChange={(e) => setSyntheticForm({ ...syntheticForm, max_package_weight_kg: parseFloat(e.target.value) || 0 })}
                    className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE]"
                  />
                </div>
              </div>

              <div>
                <label className="block font-medium text-[#29263D] mb-1">Skills (comma-separated)</label>
                <input
                  type="text"
                  value={syntheticForm.skills}
                  onChange={(e) => setSyntheticForm({ ...syntheticForm, skills: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE]"
                />
              </div>

              <div className="pt-3 border-t border-[#EAE7F2] flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowSyntheticModal(false)}
                  className="px-4 py-2 rounded-xl text-[#77748C] hover:bg-[#FAF9FE]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-[#8B7CF6] text-white font-semibold"
                >
                  Create Demo Worker
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
