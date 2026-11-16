import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  PlusCircle,
  Eye,
  CheckCircle2,
  Clock,
  AlertTriangle,
  X,
  MapPin,
  Truck,
  DollarSign,
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';
import { getTasks, getTaskDetail, createTask, validateTask } from '../api/client';

export const TasksPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [tasks, setTasks] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [taskType, setTaskType] = useState('all');
  const [priority, setPriority] = useState('all');
  const [status, setStatus] = useState('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  // Detail Drawer state
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [taskDetail, setTaskDetail] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Create Task Modal state
  const [showCreateModal, setShowCreateModal] = useState(searchParams.get('create') === 'true');
  const [formData, setFormData] = useState({
    task_type: 'delivery',
    priority: 'medium',
    pickup_lat: 18.5204,
    pickup_lon: 73.8567,
    destination_lat: 18.5304,
    destination_lon: 73.8667,
    estimated_duration_min: 45,
    deadline_min: 120,
    payment: 250,
    package_weight_kg: 5,
    vehicle_required: 'bike',
    required_skill: 'driving',
    special_handling: ''
  });
  const [validationResult, setValidationResult] = useState<any | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const res = await getTasks({
        task_type: taskType,
        priority: priority,
        status: status,
        search: search,
        page: page,
        limit: 15
      });
      setTasks(res.tasks);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, [page, taskType, priority, status]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadTasks();
  };

  const handleOpenDetail = async (taskId: string) => {
    setSelectedTaskId(taskId);
    setDetailLoading(true);
    try {
      const res = await getTaskDetail(taskId);
      setTaskDetail(res);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleValidateForm = async () => {
    try {
      const res = await validateTask(formData);
      setValidationResult(res);
    } catch (err: any) {
      setValidationResult({ valid: false, errors: [err.message] });
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    try {
      await createTask(formData);
      setShowCreateModal(false);
      setPage(1);
      loadTasks();
    } catch (err: any) {
      setCreateError(err.message || 'Failed to create task');
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top action bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#29263D]">Task Catalog & Requests</h2>
          <p className="text-xs text-[#77748C]">Search, filter, and inspect tasks available for allocation</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-sm transition-all self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>+ Create New Task</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-[#77748C] absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search tasks by ID, type, or skill..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-xs focus:outline-none focus:border-[#8B7CF6]"
          />
        </form>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* Task Type Filter */}
          <select
            value={taskType}
            onChange={(e) => { setTaskType(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
          >
            <option value="all">All Task Types</option>
            <option value="delivery">Delivery</option>
            <option value="medicine">Medicine</option>
            <option value="food">Food</option>
            <option value="fragile">Fragile</option>
            <option value="document">Document</option>
            <option value="grocery">Grocery</option>
          </select>

          {/* Priority Filter */}
          <select
            value={priority}
            onChange={(e) => { setPriority(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
          >
            <option value="all">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>

          {/* Status Filter */}
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-[#FAF9FE] rounded-xl border border-[#EAE7F2] text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
          >
            <option value="all">All Statuses</option>
            <option value="unallocated">Unallocated</option>
            <option value="allocated">Allocated</option>
          </select>
        </div>
      </div>

      {/* Task Table */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-[#FAF9FE] border-b border-[#EAE7F2] text-[#77748C]">
              <tr>
                <th className="py-3 px-4 font-semibold">Task ID</th>
                <th className="py-3 px-4 font-semibold">Type</th>
                <th className="py-3 px-4 font-semibold">Skill Needed</th>
                <th className="py-3 px-4 font-semibold">Vehicle</th>
                <th className="py-3 px-4 font-semibold">Duration / Deadline</th>
                <th className="py-3 px-4 font-semibold">Payment</th>
                <th className="py-3 px-4 font-semibold">Priority</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EAE7F2]">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-[#77748C]">
                    Loading task records...
                  </td>
                </tr>
              ) : tasks.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-[#77748C]">
                    No tasks match the filter criteria.
                  </td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <tr key={task.task_id} className="hover:bg-[#FAF9FE] transition-colors">
                    <td className="py-3 px-4 font-bold text-[#8B7CF6]">
                      {task.task_id}
                    </td>
                    <td className="py-3 px-4 font-medium text-[#29263D] capitalize">
                      {task.task_type}
                    </td>
                    <td className="py-3 px-4 text-[#77748C]">
                      <span className="px-2 py-0.5 rounded-lg bg-[#FAF9FE] border border-[#EAE7F2] font-mono text-[11px]">
                        {task.required_skill}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[#77748C] capitalize">
                      {task.vehicle_required}
                    </td>
                    <td className="py-3 px-4 text-[#77748C]">
                      {task.estimated_duration_min.toFixed(0)}m / {task.deadline_min.toFixed(0)}m
                    </td>
                    <td className="py-3 px-4 font-semibold text-[#29263D]">
                      ₹{task.payment.toFixed(0)}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                        task.priority === 'urgent' ? 'bg-red-50 text-red-700' :
                        task.priority === 'high' ? 'bg-amber-50 text-amber-700' :
                        task.priority === 'medium' ? 'bg-violet-50 text-violet-700' : 'bg-slate-50 text-slate-700'
                      }`}>
                        {task.priority}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        task.status === 'allocated' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {task.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleOpenDetail(task.task_id)}
                        className="p-1.5 rounded-lg hover:bg-[#F3F0FF] text-[#77748C] hover:text-[#8B7CF6] transition-colors"
                        title="View Task Details"
                      >
                        <Eye className="w-4 h-4 inline" />
                      </button>
                      {task.status !== 'allocated' && (
                        <button
                          onClick={() => navigate(`/allocate?task_id=${task.task_id}`)}
                          className="px-2.5 py-1 rounded-xl bg-[#F3F0FF] text-[#8B7CF6] font-semibold text-[11px] hover:bg-[#8B7CF6] hover:text-white transition-all"
                        >
                          Allocate
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-4 border-t border-[#EAE7F2] bg-[#FAF9FE] flex items-center justify-between text-xs text-[#77748C]">
          <span>Showing {tasks.length} of {total} tasks</span>
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
              disabled={tasks.length < 15}
              className="px-3 py-1.5 rounded-xl border border-[#EAE7F2] bg-white disabled:opacity-40 hover:bg-[#FAF9FE]"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Task Detail Drawer */}
      {selectedTaskId && (
        <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-lg bg-white h-full shadow-2xl p-6 overflow-y-auto space-y-6 animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-[#EAE7F2]">
              <div>
                <span className="text-xs text-[#77748C] uppercase tracking-wider font-semibold">Task Detail Drawer</span>
                <h3 className="text-lg font-bold text-[#29263D]">{selectedTaskId}</h3>
              </div>
              <button
                onClick={() => setSelectedTaskId(null)}
                className="p-2 rounded-xl text-[#77748C] hover:bg-[#F3F0FF]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {detailLoading || !taskDetail ? (
              <p className="text-xs text-[#77748C] text-center py-12">Loading details...</p>
            ) : (
              <div className="space-y-5 text-xs">
                {/* Status banner */}
                <div className={`p-4 rounded-2xl border ${
                  taskDetail.task.status === 'allocated' ? 'bg-emerald-50 border-emerald-200' : 'bg-[#F3F0FF] border-violet-200'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs uppercase tracking-wider">
                      Status: {taskDetail.task.status}
                    </span>
                    {taskDetail.task.status === 'allocated' && (
                      <span className="text-emerald-800 font-semibold text-[11px]">Assigned to {taskDetail.task.allocated_worker_id}</span>
                    )}
                  </div>
                  {taskDetail.allocation && (
                    <p className="mt-2 text-[#77748C] text-[11px] leading-relaxed">
                      {taskDetail.allocation.explanation}
                    </p>
                  )}
                </div>

                {/* Parameters Grid */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] uppercase font-bold">Category</span>
                    <p className="font-bold text-sm text-[#29263D] capitalize mt-0.5">{taskDetail.task.task_type}</p>
                  </div>
                  <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] uppercase font-bold">Required Skill</span>
                    <p className="font-bold text-sm text-[#8B7CF6] font-mono mt-0.5">{taskDetail.task.required_skill}</p>
                  </div>
                  <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] uppercase font-bold">Vehicle Requirement</span>
                    <p className="font-bold text-sm text-[#29263D] capitalize mt-0.5">{taskDetail.task.vehicle_required}</p>
                  </div>
                  <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] uppercase font-bold">Package Weight</span>
                    <p className="font-bold text-sm text-[#29263D] mt-0.5">{taskDetail.task.package_weight_kg} kg</p>
                  </div>
                  <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] uppercase font-bold">Duration / Deadline</span>
                    <p className="font-bold text-sm text-[#29263D] mt-0.5">{taskDetail.task.estimated_duration_min.toFixed(0)}m / {taskDetail.task.deadline_min.toFixed(0)}m</p>
                  </div>
                  <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
                    <span className="text-[10px] text-[#77748C] uppercase font-bold">Reward / Payment</span>
                    <p className="font-bold text-sm text-emerald-700 mt-0.5">₹{taskDetail.task.payment.toFixed(2)}</p>
                  </div>
                </div>

                {/* Coordinates */}
                <div className="p-4 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] space-y-2">
                  <span className="text-[10px] text-[#77748C] uppercase font-bold flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-[#8B7CF6]" /> Geographic Coordinates
                  </span>
                  <div className="flex items-center justify-between text-[#29263D]">
                    <span>Pickup: [{taskDetail.task.pickup_lat.toFixed(4)}, {taskDetail.task.pickup_lon.toFixed(4)}]</span>
                    <span>Destination: [{taskDetail.task.destination_lat.toFixed(4)}, {taskDetail.task.destination_lon.toFixed(4)}]</span>
                  </div>
                </div>

                {/* Actions inside drawer */}
                <div className="pt-4 flex items-center justify-end gap-3">
                  {taskDetail.task.status !== 'allocated' ? (
                    <button
                      onClick={() => navigate(`/allocate?task_id=${taskDetail.task.task_id}`)}
                      className="w-full py-2.5 rounded-2xl bg-[#8B7CF6] text-white font-semibold text-xs shadow-sm hover:bg-[#7A6AE6] transition-all flex items-center justify-center gap-2"
                    >
                      <span>Proceed to Allocation</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      onClick={() => navigate(`/history`)}
                      className="w-full py-2.5 rounded-2xl bg-[#F3F0FF] text-[#8B7CF6] font-semibold text-xs hover:bg-[#EAE7F2] transition-all"
                    >
                      View in Allocation History
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 6.3 Create Task Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl border border-[#EAE7F2] shadow-2xl max-w-xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-[#EAE7F2] flex items-center justify-between sticky top-0 bg-white z-10">
              <div>
                <h3 className="font-bold text-base text-[#29263D]">Create New Task</h3>
                <p className="text-xs text-[#77748C]">Provide task requirements for ML & fairness matching</p>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 rounded-xl text-[#77748C] hover:bg-[#F3F0FF]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="p-6 space-y-4 text-xs">
              {createError && (
                <div className="p-3 rounded-xl bg-red-50 text-red-700 text-xs border border-red-200">
                  {createError}
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-medium text-[#29263D] mb-1">Task Category</label>
                  <select
                    value={formData.task_type}
                    onChange={(e) => setFormData({ ...formData, task_type: e.target.value })}
                    className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
                  >
                    <option value="delivery">Delivery</option>
                    <option value="medicine">Medicine</option>
                    <option value="food">Food</option>
                    <option value="fragile">Fragile</option>
                    <option value="document">Document</option>
                    <option value="grocery">Grocery</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-[#29263D] mb-1">Priority</label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-medium text-[#29263D] mb-1">Required Skill</label>
                  <select
                    value={formData.required_skill}
                    onChange={(e) => setFormData({ ...formData, required_skill: e.target.value })}
                    className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
                  >
                    <option value="driving">driving</option>
                    <option value="navigation">navigation</option>
                    <option value="handling">handling</option>
                    <option value="customer_service">customer_service</option>
                    <option value="time_management">time_management</option>
                    <option value="cold_chain">cold_chain</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-[#29263D] mb-1">Vehicle Requirement</label>
                  <select
                    value={formData.vehicle_required}
                    onChange={(e) => setFormData({ ...formData, vehicle_required: e.target.value })}
                    className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
                  >
                    <option value="none">None</option>
                    <option value="bike">Bike</option>
                    <option value="scooter">Scooter</option>
                    <option value="car">Car</option>
                    <option value="van">Van</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-medium text-[#29263D] mb-1">Est. Duration (m)</label>
                  <input
                    type="number"
                    value={formData.estimated_duration_min}
                    onChange={(e) => setFormData({ ...formData, estimated_duration_min: parseFloat(e.target.value) || 0 })}
                    className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
                  />
                </div>
                <div>
                  <label className="block font-medium text-[#29263D] mb-1">Deadline (m)</label>
                  <input
                    type="number"
                    value={formData.deadline_min}
                    onChange={(e) => setFormData({ ...formData, deadline_min: parseFloat(e.target.value) || 0 })}
                    className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
                  />
                </div>
                <div>
                  <label className="block font-medium text-[#29263D] mb-1">Payment (₹)</label>
                  <input
                    type="number"
                    value={formData.payment}
                    onChange={(e) => setFormData({ ...formData, payment: parseFloat(e.target.value) || 0 })}
                    className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
                  />
                </div>
              </div>

              <div>
                <label className="block font-medium text-[#29263D] mb-1">Package Weight (kg)</label>
                <input
                  type="number"
                  step="0.5"
                  value={formData.package_weight_kg}
                  onChange={(e) => setFormData({ ...formData, package_weight_kg: parseFloat(e.target.value) || 0 })}
                  className="w-full p-2.5 rounded-xl border border-[#EAE7F2] bg-[#FAF9FE] focus:outline-none focus:border-[#8B7CF6]"
                />
              </div>

              {/* Validation Feedback Box */}
              {validationResult && (
                <div className={`p-3 rounded-2xl border ${
                  validationResult.valid ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'
                }`}>
                  <p className="font-bold text-xs">
                    {validationResult.valid ? '✓ Validation Passed' : '⚠ Validation Issues Found'}
                  </p>
                  {validationResult.errors?.map((err: string, i: number) => (
                    <p key={i} className="text-[11px] mt-0.5">• {err}</p>
                  ))}
                  {validationResult.warnings?.map((w: string, i: number) => (
                    <p key={i} className="text-[11px] mt-0.5 text-amber-700">• {w}</p>
                  ))}
                </div>
              )}

              <div className="pt-4 border-t border-[#EAE7F2] flex items-center justify-between">
                <button
                  type="button"
                  onClick={handleValidateForm}
                  className="px-3.5 py-2 rounded-xl bg-[#FAF9FE] border border-[#EAE7F2] text-[#29263D] hover:bg-[#F3F0FF] font-semibold text-xs"
                >
                  Validate Task
                </button>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 rounded-xl text-[#77748C] hover:bg-[#FAF9FE] font-medium text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 rounded-xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-xs"
                  >
                    Create Task
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
