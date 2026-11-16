import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Check,
  ChevronRight,
  Sparkles,
  AlertTriangle,
  UserCheck,
  BrainCircuit,
  Scale,
  Award,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
  Sliders,
  Info,
  CheckCircle2,
  FileSpreadsheet
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { getTasks, getTaskDetail, previewAllocation, runAllocation } from '../api/client';
import { ExplainableAIPanel } from '../components/ExplainableAIPanel';

export const AllocatePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [currentStep, setCurrentStep] = useState(1);
  const [tasks, setTasks] = useState<any[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string>(searchParams.get('task_id') || '');
  const [taskDetail, setTaskDetail] = useState<any | null>(null);

  // Allocation parameters
  const [lambdaVal, setLambdaVal] = useState<number>(0.08);
  const [policy, setPolicy] = useState<string>('WAFR');

  // Evaluation results
  const [evaluationResult, setEvaluationResult] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [confirming, setConfirming] = useState<boolean>(false);
  const [confirmedAllocationId, setConfirmedAllocationId] = useState<string | null>(null);

  // Load task list on mount
  useEffect(() => {
    getTasks({ status: 'unallocated', limit: 50 }).then((res) => {
      setTasks(res.tasks);
      if (!selectedTaskId && res.tasks.length > 0) {
        setSelectedTaskId(res.tasks[0].task_id);
      }
    });
  }, []);

  // Load task detail when selected
  useEffect(() => {
    if (selectedTaskId) {
      getTaskDetail(selectedTaskId).then((res) => setTaskDetail(res.task));
    }
  }, [selectedTaskId]);

  const handleRunEvaluation = async (targetStep: number = 2) => {
    setLoading(true);
    try {
      const res = await previewAllocation({
        task_id: selectedTaskId,
        lambda_val: lambdaVal,
        policy: policy
      });
      setEvaluationResult(res);
      setCurrentStep(targetStep);
    } catch (err: any) {
      alert(err.message || 'Error evaluating candidates');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAllocation = async () => {
    if (!evaluationResult?.selected_worker) return;
    if (!window.confirm(`Confirm assigning Task ${selectedTaskId} to Worker ${evaluationResult.selected_worker.worker_id}?`)) {
      return;
    }

    setConfirming(true);
    try {
      const res = await runAllocation({
        task_id: selectedTaskId,
        lambda_val: lambdaVal,
        policy: policy,
        confirm: true
      });
      setConfirmedAllocationId(res.allocation_id);
    } catch (err: any) {
      alert(err.message || 'Error confirming allocation');
    } finally {
      setConfirming(false);
    }
  };

  const steps = [
    { num: 1, title: 'Select Task' },
    { num: 2, title: 'Evaluate Workers' },
    { num: 3, title: 'ML Predictions' },
    { num: 4, title: 'Fairness Signals' },
    { num: 5, title: 'Final Allocation' }
  ];

  return (
    <div className="space-y-6 pb-16">
      {/* Stepper Header */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] p-5 shadow-xs">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          {steps.map((s, idx) => {
            const isActive = currentStep === s.num;
            const isDone = currentStep > s.num;
            return (
              <React.Fragment key={s.num}>
                <div
                  className={`flex items-center space-x-2 transition-all ${
                    evaluationResult ? 'cursor-pointer hover:opacity-80' : ''
                  }`}
                  onClick={() => {
                    if (evaluationResult) {
                      setCurrentStep(s.num);
                    }
                  }}
                  title={evaluationResult ? `Click to jump to Step ${s.num}: ${s.title}` : undefined}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs transition-colors ${
                      isDone
                        ? 'bg-emerald-100 text-emerald-800'
                        : isActive
                        ? 'bg-[#8B7CF6] text-white shadow-sm'
                        : 'bg-[#F3F0FF] text-[#77748C]'
                    }`}
                  >
                    {isDone ? <Check className="w-4 h-4" /> : s.num}
                  </div>
                  <span className={`text-xs font-semibold hidden md:inline ${
                    isActive ? 'text-[#29263D]' : 'text-[#77748C]'
                  }`}>
                    {s.title}
                  </span>
                </div>
                {idx < steps.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-2 ${
                    currentStep > s.num ? 'bg-emerald-300' : 'bg-[#EAE7F2]'
                  }`} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* STEP 1: SELECT OR CREATE TASK */}
      {currentStep === 1 && (
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200">
          <div>
            <h3 className="text-lg font-bold text-[#29263D]">Step 1: Select or Create Task</h3>
            <p className="text-xs text-[#77748C]">Choose a task from the active catalog to run worker suitability, ML prediction, and fairness allocation.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#29263D] mb-1.5">Choose Task</label>
              <select
                value={selectedTaskId}
                onChange={(e) => setSelectedTaskId(e.target.value)}
                className="w-full p-3 rounded-2xl border border-[#EAE7F2] bg-[#FAF9FE] text-xs font-medium text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
              >
                {tasks.map((t) => (
                  <option key={t.task_id} value={t.task_id}>
                    {t.task_id} — {t.task_type.toUpperCase()} ({t.required_skill}, ₹{t.payment.toFixed(0)})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#29263D] mb-1.5">Allocation Policy</label>
              <select
                value={policy}
                onChange={(e) => setPolicy(e.target.value)}
                className="w-full p-3 rounded-2xl border border-[#EAE7F2] bg-[#FAF9FE] text-xs font-medium text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
              >
                <option value="WAFR">WAFR (Workload-Aware Fair Ranking)</option>
                <option value="ML-Only">ML-Only (Pure Success Probability)</option>
                <option value="Nearest Eligible">Nearest Eligible (Operational Distance)</option>
              </select>
            </div>
          </div>

          {/* Task preview card */}
          {taskDetail && (
            <div className="p-5 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-[#29263D]">Task Profile: {taskDetail.task_id}</span>
                <span className="px-2.5 py-1 rounded-full bg-[#F3F0FF] text-[#8B7CF6] font-semibold text-[11px] uppercase">
                  {taskDetail.task_type}
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-[#77748C]">
                <div>
                  <span className="text-[10px] uppercase font-bold block">Required Skill</span>
                  <strong className="text-[#29263D] font-mono">{taskDetail.required_skill}</strong>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold block">Vehicle</span>
                  <strong className="text-[#29263D] capitalize">{taskDetail.vehicle_required}</strong>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold block">Package</span>
                  <strong className="text-[#29263D]">{taskDetail.package_weight_kg} kg</strong>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold block">Duration / Deadline</span>
                  <strong className="text-[#29263D]">{taskDetail.estimated_duration_min.toFixed(0)}m / {taskDetail.deadline_min.toFixed(0)}m</strong>
                </div>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-[#EAE7F2]">
            <button
              onClick={() => navigate('/tasks?create=true')}
              className="px-4 py-2 text-xs font-semibold text-[#8B7CF6] hover:underline"
            >
              + Create New Task Instead
            </button>
            <button
              onClick={() => handleRunEvaluation(2)}
              disabled={loading || !selectedTaskId}
              className="flex items-center gap-2 px-6 py-2.5 rounded-2xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-sm transition-all disabled:opacity-50"
            >
              <span>{loading ? 'Evaluating...' : 'Continue to Worker Evaluation'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: EVALUATE WORKERS & ELIGIBILITY */}
      {currentStep === 2 && evaluationResult && (
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200">
          <div>
            <h3 className="text-lg font-bold text-[#29263D]">Step 2: Candidate Eligibility Evaluation</h3>
            <p className="text-xs text-[#77748C]">Worker suitability agent checked hard feasibility constraints across registered workers.</p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-[#F3F0FF] border border-violet-100 text-center">
              <span className="text-xs text-[#77748C]">Candidates Examined</span>
              <h4 className="text-2xl font-bold text-[#8B7CF6] mt-1">{evaluationResult.total_candidates_examined}</h4>
            </div>
            <div className="p-4 rounded-2xl bg-[#D9F3E4] border border-emerald-100 text-center">
              <span className="text-xs text-emerald-800">Eligible Candidates</span>
              <h4 className="text-2xl font-bold text-emerald-700 mt-1">{evaluationResult.eligible_count}</h4>
            </div>
            <div className="p-4 rounded-2xl bg-[#F8DDE8] border border-pink-100 text-center">
              <span className="text-xs text-pink-800">Ineligible Candidates</span>
              <h4 className="text-2xl font-bold text-pink-700 mt-1">{evaluationResult.ineligible_count}</h4>
            </div>
          </div>

          {/* Breakdown of Ineligibility */}
          <div className="p-5 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] space-y-3">
            <h4 className="font-bold text-xs text-[#29263D] uppercase tracking-wider">Candidate Rejection Analysis</h4>
            <p className="text-xs text-[#77748C]">
              Ineligible candidates were safely filtered out due to hard constraints (e.g., missing mandatory skill, incompatible vehicle type, package capacity limit, or deadline infeasibility).
            </p>
            <div className="space-y-2 mt-2">
              {evaluationResult.top_candidates
                .filter((c: any) => !c.eligible)
                .slice(0, 4)
                .map((c: any) => (
                  <div key={c.worker_id} className="p-2.5 rounded-xl bg-white border border-[#EAE7F2] text-xs flex items-center justify-between">
                    <div>
                      <strong className="text-[#29263D]">{c.worker_id}</strong>
                      <span className="text-[#77748C] ml-2">({c.vehicle_type}, {c.availability_status})</span>
                    </div>
                    <span className="text-red-700 text-[11px] font-medium">
                      {c.ineligibility_reasons[0] || 'Infeasible'}
                    </span>
                  </div>
                ))}
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-[#EAE7F2]">
            <button
              onClick={() => setCurrentStep(1)}
              className="px-4 py-2 rounded-xl border border-[#EAE7F2] text-xs font-semibold text-[#77748C] hover:bg-[#FAF9FE]"
            >
              Back
            </button>
            <button
              onClick={() => setCurrentStep(3)}
              disabled={evaluationResult.eligible_count === 0}
              className="flex items-center gap-2 px-6 py-2.5 rounded-2xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-sm transition-all disabled:opacity-50"
            >
              <span>Run ML Predictions</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: ML PREDICTION */}
      {currentStep === 3 && evaluationResult && (
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-[#29263D]">Step 3: Machine Learning Success Likelihood</h3>
              <p className="text-xs text-[#77748C]">
                HistGradientBoosting (weight 0.5) + CatBoost (weight 0.5) evaluated 27 features for all eligible candidates.
              </p>
            </div>
            <span className="px-3 py-1 rounded-full bg-violet-50 text-violet-700 text-xs font-semibold border border-violet-100">
              Ensemble Threshold: 0.155
            </span>
          </div>

          {/* Probability Distribution Chart */}
          <div className="h-48 bg-[#FAF9FE] rounded-2xl p-4 border border-[#EAE7F2]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={evaluationResult.top_candidates.filter((c: any) => c.eligible).slice(0, 10)}
                margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
              >
                <XAxis dataKey="worker_id" tick={{ fontSize: 11, fill: '#77748C' }} />
                <YAxis tick={{ fontSize: 11, fill: '#77748C' }} domain={[0, 1]} />
                <Tooltip />
                <Bar dataKey="predicted_success" fill="#8B7CF6" radius={[6, 6, 0, 0]} name="Predicted Success" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Ranked table */}
          <div className="overflow-x-auto rounded-2xl border border-[#EAE7F2]">
            <table className="w-full text-xs text-left">
              <thead className="bg-[#FAF9FE] border-b border-[#EAE7F2] text-[#77748C]">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Rank</th>
                  <th className="py-2.5 px-3 font-semibold">Worker ID</th>
                  <th className="py-2.5 px-3 font-semibold">P(Success)</th>
                  <th className="py-2.5 px-3 font-semibold">HGB / CatBoost</th>
                  <th className="py-2.5 px-3 font-semibold">Distance</th>
                  <th className="py-2.5 px-3 font-semibold">Experience</th>
                  <th className="py-2.5 px-3 font-semibold">7d Workload</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE7F2]">
                {evaluationResult.top_candidates
                  .filter((c: any) => c.eligible)
                  .slice(0, 6)
                  .map((c: any) => (
                    <tr key={c.worker_id} className="hover:bg-[#FAF9FE]">
                      <td className="py-2.5 px-3 font-bold text-[#8B7CF6]">#{c.rank}</td>
                      <td className="py-2.5 px-3 font-semibold text-[#29263D]">{c.worker_id}</td>
                      <td className="py-2.5 px-3 font-bold text-emerald-700">
                        {(c.predicted_success * 100).toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-3 text-[#77748C] font-mono text-[11px]">
                        {c.hgb_prob?.toFixed(3)} / {c.cat_prob?.toFixed(3)}
                      </td>
                      <td className="py-2.5 px-3 text-[#77748C]">{c.distance_km} km</td>
                      <td className="py-2.5 px-3 text-[#77748C]">{c.experience_years.toFixed(1)} yrs</td>
                      <td className="py-2.5 px-3 text-[#77748C]">{c.current_workload_hours.toFixed(1)} hrs</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-[#EAE7F2]">
            <button
              onClick={() => setCurrentStep(2)}
              className="px-4 py-2 rounded-xl border border-[#EAE7F2] text-xs font-semibold text-[#77748C] hover:bg-[#FAF9FE]"
            >
              Back
            </button>
            <button
              onClick={() => setCurrentStep(4)}
              className="flex items-center gap-2 px-6 py-2.5 rounded-2xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-sm transition-all"
            >
              <span>Evaluate Fairness</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: FAIRNESS EVALUATION & LAMBDA CONFIG */}
      {currentStep === 4 && evaluationResult && (
        <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200">
          <div>
            <h3 className="text-lg font-bold text-[#29263D]">Step 4: Fairness Evaluation & λ Tuning</h3>
            <p className="text-xs text-[#77748C]">
              Incorporate worker opportunity credits and workload pressure penalties into the multi-objective ranking.
            </p>
          </div>

          {/* Lambda Configurator */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-[#F3F0FF] to-white border border-[#EAE7F2] space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[#8B7CF6]" />
                <span className="font-bold text-xs text-[#29263D]">Fairness Coefficient (λ)</span>
              </div>
              <span className="px-3 py-1 bg-white font-mono font-bold text-[#8B7CF6] rounded-xl border border-[#EAE7F2] text-xs">
                λ = {lambdaVal.toFixed(2)}
              </span>
            </div>

            <input
              type="range"
              min="0.0"
              max="0.40"
              step="0.02"
              value={lambdaVal}
              onChange={(e) => setLambdaVal(parseFloat(e.target.value))}
              className="w-full accent-[#8B7CF6] cursor-pointer"
            />

            <div className="flex items-center justify-between text-[11px] text-[#77748C]">
              <span>λ = 0.00 (Efficiency/Success Dominant)</span>
              <span className="font-semibold text-[#8B7CF6]">0.08 (Recommended Baseline)</span>
              <span>λ = 0.40 (High Equity Priority)</span>
            </div>
          </div>

          {/* Formula Breakdown Visualization */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs">
            <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
              <span className="text-[10px] text-[#77748C] uppercase font-bold block">ML Weight</span>
              <h4 className="font-bold text-sm text-[#8B7CF6] mt-0.5">+ 70%</h4>
              <span className="text-[10px] text-[#77748C]">Predicted success</span>
            </div>
            <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
              <span className="text-[10px] text-[#77748C] uppercase font-bold block">Efficiency Weight</span>
              <h4 className="font-bold text-sm text-[#3B82F6] mt-0.5">+ 30%</h4>
              <span className="text-[10px] text-[#77748C]">Distance & deadline</span>
            </div>
            <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
              <span className="text-[10px] text-[#77748C] uppercase font-bold block">Opportunity Credit</span>
              <h4 className="font-bold text-sm text-emerald-700 mt-0.5">+ {(lambdaVal * 100).toFixed(0)}%</h4>
              <span className="text-[10px] text-[#77748C]">Starvation relief</span>
            </div>
            <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
              <span className="text-[10px] text-[#77748C] uppercase font-bold block">Workload Penalty</span>
              <h4 className="font-bold text-sm text-pink-700 mt-0.5">- {(lambdaVal * 100).toFixed(0)}%</h4>
              <span className="text-[10px] text-[#77748C]">Burnout prevention</span>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-[#EAE7F2]">
            <button
              onClick={() => setCurrentStep(3)}
              className="px-4 py-2 rounded-xl border border-[#EAE7F2] text-xs font-semibold text-[#77748C] hover:bg-[#FAF9FE]"
            >
              Back
            </button>
            <button
              onClick={() => handleRunEvaluation(5)}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2.5 rounded-2xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-sm transition-all disabled:opacity-50"
            >
              <span>{loading ? 'Calculating...' : 'Calculate Final Allocation (Step 5)'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: FINAL ALLOCATION & CONFIRMATION */}
      {currentStep === 5 && evaluationResult && (
        <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200">
          {evaluationResult.selected_worker ? (
            <>
              {/* Prominent Winner Decision Card */}
              <div className="bg-gradient-to-r from-violet-500 to-[#8B7CF6] rounded-3xl p-6 sm:p-8 text-white shadow-lg space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md text-xs font-semibold">
                    <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                    <span>Recommended Assignment via {policy} (λ = {lambdaVal.toFixed(2)})</span>
                  </div>
                  {confirmedAllocationId && (
                    <span className="px-3 py-1 rounded-full bg-emerald-400/30 text-emerald-100 font-mono text-xs font-bold border border-emerald-300/40">
                      Confirmed: {confirmedAllocationId}
                    </span>
                  )}
                </div>

                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                  <div>
                    <span className="text-white/80 text-xs uppercase tracking-wider font-semibold">Selected Worker</span>
                    <h2 className="text-3xl font-extrabold tracking-tight mt-1">
                      Worker {evaluationResult.selected_worker.worker_id}
                    </h2>
                    <p className="text-white/80 text-xs mt-1">
                      Vehicle: {evaluationResult.selected_worker.vehicle_type} • Experience: {evaluationResult.selected_worker.experience_years.toFixed(1)} yrs • Distance: {evaluationResult.selected_worker.distance_km} km
                    </p>
                  </div>

                  <div className="flex items-center gap-4 bg-white/10 backdrop-blur-md p-4 rounded-2xl border border-white/20">
                    <div>
                      <span className="text-white/70 text-[10px] uppercase font-bold block">P(Success)</span>
                      <strong className="text-xl font-bold">
                        {(evaluationResult.selected_worker.predicted_success * 100).toFixed(1)}%
                      </strong>
                    </div>
                    <div className="h-8 w-px bg-white/20" />
                    <div>
                      <span className="text-white/70 text-[10px] uppercase font-bold block">WAFR Score</span>
                      <strong className="text-xl font-bold text-amber-300">
                        {evaluationResult.selected_worker.wafr_score}
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Score Decomposition */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-white/20 text-xs">
                  <div>
                    <span className="text-white/70 text-[10px] uppercase font-bold block">ML Contribution</span>
                    <strong className="text-sm font-semibold">
                      +{(0.70 * evaluationResult.selected_worker.predicted_success).toFixed(3)}
                    </strong>
                  </div>
                  <div>
                    <span className="text-white/70 text-[10px] uppercase font-bold block">Efficiency Term</span>
                    <strong className="text-sm font-semibold">
                      +{(0.30 * evaluationResult.selected_worker.efficiency).toFixed(3)}
                    </strong>
                  </div>
                  <div>
                    <span className="text-white/70 text-[10px] uppercase font-bold block">Opportunity Credit</span>
                    <strong className="text-sm font-semibold">
                      +{(lambdaVal * evaluationResult.selected_worker.opportunity_credit).toFixed(3)}
                    </strong>
                  </div>
                  <div>
                    <span className="text-white/70 text-[10px] uppercase font-bold block">Workload Penalty</span>
                    <strong className="text-sm font-semibold text-rose-200">
                      -{(lambdaVal * evaluationResult.selected_worker.workload_pressure).toFixed(3)}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Data-Grounded Explanation & LLM-Powered XAI */}
              <ExplainableAIPanel
                taskId={selectedTaskId}
                selectedWorker={evaluationResult.selected_worker}
                runnerUp={
                  evaluationResult.top_candidates?.find(
                    (c: any) => c.worker_id !== evaluationResult.selected_worker?.worker_id && c.eligible
                  )
                }
                policy={policy}
                lambdaVal={lambdaVal}
              />

              {/* Candidate Comparison Table */}
              <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs space-y-4">
                <h4 className="font-bold text-sm text-[#29263D]">Top Eligible Candidate Rankings</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-[#FAF9FE] border-b border-[#EAE7F2] text-[#77748C]">
                      <tr>
                        <th className="py-2.5 px-3">Rank</th>
                        <th className="py-2.5 px-3">Worker ID</th>
                        <th className="py-2.5 px-3">WAFR Score</th>
                        <th className="py-2.5 px-3">P(Success)</th>
                        <th className="py-2.5 px-3">Efficiency</th>
                        <th className="py-2.5 px-3">Opportunity</th>
                        <th className="py-2.5 px-3">Workload</th>
                        <th className="py-2.5 px-3">Distance</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#EAE7F2]">
                      {evaluationResult.top_candidates
                        .filter((c: any) => c.eligible)
                        .slice(0, 6)
                        .map((c: any) => (
                          <tr key={c.worker_id} className={`hover:bg-[#FAF9FE] ${
                            c.rank === 1 ? 'bg-violet-50/50 font-semibold' : ''
                          }`}>
                            <td className="py-2.5 px-3 font-bold text-[#8B7CF6]">#{c.rank}</td>
                            <td className="py-2.5 px-3 font-bold text-[#29263D]">{c.worker_id}</td>
                            <td className="py-2.5 px-3 font-bold text-[#8B7CF6]">{c.wafr_score}</td>
                            <td className="py-2.5 px-3">{(c.predicted_success * 100).toFixed(1)}%</td>
                            <td className="py-2.5 px-3 text-[#77748C]">{c.efficiency}</td>
                            <td className="py-2.5 px-3 text-[#77748C]">{c.opportunity_credit}</td>
                            <td className="py-2.5 px-3 text-[#77748C]">{c.workload_pressure}</td>
                            <td className="py-2.5 px-3 text-[#77748C]">{c.distance_km} km</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                <button
                  onClick={() => setCurrentStep(1)}
                  className="px-4 py-2.5 rounded-2xl border border-[#EAE7F2] text-xs font-semibold text-[#77748C] hover:bg-[#FAF9FE] flex items-center gap-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Start New Allocation</span>
                </button>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => navigate('/history')}
                    className="px-4 py-2.5 rounded-2xl border border-[#EAE7F2] text-xs font-semibold text-[#29263D] hover:bg-[#F3F0FF]"
                  >
                    View History
                  </button>
                  <button
                    onClick={handleConfirmAllocation}
                    disabled={confirming || !!confirmedAllocationId}
                    className="px-6 py-2.5 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-sm transition-all disabled:opacity-50 flex items-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{confirmedAllocationId ? 'Allocation Confirmed!' : (confirming ? 'Saving...' : 'Confirm Assignment')}</span>
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-3xl border border-red-200 p-8 text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-red-900">No Eligible Workers Found</h3>
              <p className="text-xs text-[#77748C] max-w-md mx-auto leading-relaxed">
                All candidates examined failed mandatory constraints (skills, vehicle requirements, capacity, or travel deadline). In accordance with FairGig principles, no ineligible worker has been assigned.
              </p>
              <button
                onClick={() => setCurrentStep(1)}
                className="px-5 py-2.5 rounded-2xl bg-[#8B7CF6] text-white font-semibold text-xs hover:bg-[#7A6AE6]"
              >
                Select Another Task
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
