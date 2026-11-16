import React, { useState, useEffect } from 'react';
import {
  Layers,
  Play,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  UserCheck,
  BrainCircuit,
  Scale,
  Award,
  Sparkles,
  Info,
  X,
  RefreshCw,
  Cpu,
  ChevronRight
} from 'lucide-react';
import { getAgentsStatus, runAgentsWorkflow, getTasks } from '../api/client';

export const AgentsPage: React.FC = () => {
  const [pipeline, setPipeline] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string>('T00000');
  const [lambdaVal, setLambdaVal] = useState<number>(0.08);

  const [running, setRunning] = useState<boolean>(false);
  const [executionResult, setExecutionResult] = useState<any | null>(null);
  const [selectedAgentDetail, setSelectedAgentDetail] = useState<any | null>(null);

  // Load initial pipeline and task list
  useEffect(() => {
    getAgentsStatus().then((res) => setPipeline(res.pipeline));
    getTasks({ status: 'unallocated', limit: 20 }).then((res) => {
      setTasks(res.tasks);
      if (res.tasks.length > 0) {
        setSelectedTaskId(res.tasks[0].task_id);
      }
    });
  }, []);

  const handleRunWorkflow = async () => {
    if (!selectedTaskId) return;
    setRunning(true);
    setExecutionResult(null);
    try {
      const res = await runAgentsWorkflow({
        task_id: selectedTaskId,
        lambda_val: lambdaVal,
        policy: 'WAFR',
        max_candidates: 100
      });
      setExecutionResult(res);

      // Merge executed status into pipeline view
      if (res.stages) {
        setPipeline((prev) =>
          prev.map((agent) => {
            const executed = res.stages.find((s: any) => s.agent_id === agent.agent_id);
            if (executed) {
              return {
                ...agent,
                status: executed.status,
                duration_ms: executed.duration_ms,
                last_input: executed.input_summary,
                last_output: executed.output_summary,
                error_message: executed.error_message
              };
            }
            return agent;
          })
        );
      }
    } catch (err: any) {
      alert(err.message || 'Error executing agent pipeline');
    } finally {
      setRunning(false);
    }
  };

  const getAgentIcon = (id: string) => {
    switch (id) {
      case 'agent_task_analysis':
        return FileText;
      case 'agent_worker_suitability':
        return UserCheck;
      case 'service_ml_prediction':
        return BrainCircuit;
      case 'agent_fairness_evaluation':
        return Scale;
      case 'agent_allocation':
        return Award;
      case 'agent_explainability':
        return Sparkles;
      default:
        return Cpu;
    }
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Header and Controls */}
      <div className="bg-white rounded-3xl border border-[#EAE7F2] p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <h2 className="text-xl font-bold text-[#29263D]">Multi-Agent Orchestration Architecture</h2>
          </div>
          <p className="text-xs text-[#77748C] mt-1">
            End-to-end autonomous agent workflow with explicit ML prediction and transparency services.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedTaskId}
            onChange={(e) => setSelectedTaskId(e.target.value)}
            className="px-3.5 py-2 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] text-xs font-medium text-[#29263D] focus:outline-none focus:border-[#8B7CF6]"
          >
            {tasks.map((t) => (
              <option key={t.task_id} value={t.task_id}>
                {t.task_id} ({t.task_type.toUpperCase()})
              </option>
            ))}
          </select>

          <button
            onClick={handleRunWorkflow}
            disabled={running || !selectedTaskId}
            className="flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-semibold text-xs shadow-sm transition-all disabled:opacity-50"
          >
            {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
            <span>{running ? 'Executing Pipeline...' : 'Run Live Workflow'}</span>
          </button>
        </div>
      </div>

      {/* Execution Performance Banner */}
      {executionResult && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-3xl p-5 text-emerald-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs animate-in fade-in duration-200">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-700" />
            <div>
              <strong className="block text-sm">Pipeline Execution Completed</strong>
              <span>
                Task {executionResult.task_id} processed across all 6 stages in <strong>{executionResult.total_duration_ms} ms</strong>.
              </span>
            </div>
          </div>
          {executionResult.selected_worker && (
            <span className="px-3 py-1 bg-white text-emerald-800 font-semibold rounded-xl border border-emerald-200 text-center">
              Selected: {executionResult.selected_worker.worker_id} (WAFR: {executionResult.selected_worker.wafr_score})
            </span>
          )}
        </div>
      )}

      {/* Visual Agent Workflow Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {pipeline.map((agent, index) => {
          const Icon = getAgentIcon(agent.agent_id);
          const isML = agent.agent_id === 'service_ml_prediction';

          return (
            <div
              key={agent.agent_id}
              className={`bg-white rounded-3xl border transition-all duration-200 p-5 shadow-xs flex flex-col justify-between ${
                agent.status === 'Completed'
                  ? 'border-emerald-200 hover:border-emerald-300'
                  : agent.status === 'Failed'
                  ? 'border-red-200'
                  : 'border-[#EAE7F2] hover:border-[#8B7CF6]'
              }`}
            >
              <div>
                {/* Card Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 rounded-2xl flex items-center justify-center ${
                      isML ? 'bg-[#DCEBFA] text-blue-600' : 'bg-[#F3F0FF] text-[#8B7CF6]'
                    }`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-[#77748C] uppercase tracking-wider block">
                        Stage {index + 1} • {agent.type || 'Agent'}
                      </span>
                      <h4 className="font-bold text-sm text-[#29263D] leading-tight mt-0.5">
                        {agent.name.split(':')[1] || agent.name}
                      </h4>
                    </div>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                    agent.status === 'Completed'
                      ? 'bg-emerald-50 text-emerald-700'
                      : agent.status === 'Running'
                      ? 'bg-violet-50 text-[#8B7CF6] animate-pulse'
                      : agent.status === 'Failed'
                      ? 'bg-red-50 text-red-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {agent.status}
                  </span>
                </div>

                {/* Purpose */}
                <p className="text-xs text-[#77748C] mt-3 leading-relaxed">
                  {agent.purpose}
                </p>

                {/* Specs */}
                <div className="mt-4 pt-3 border-t border-[#EAE7F2] space-y-1.5 text-[11px]">
                  <div>
                    <span className="text-[#77748C] font-semibold">Inputs: </span>
                    <span className="text-[#29263D]">{agent.input_spec}</span>
                  </div>
                  <div>
                    <span className="text-[#77748C] font-semibold">Outputs: </span>
                    <span className="text-[#29263D]">{agent.output_spec}</span>
                  </div>
                  {agent.duration_ms !== undefined && (
                    <div className="flex items-center gap-1 text-[#8B7CF6] font-medium pt-1">
                      <Clock className="w-3 h-3" />
                      <span>Execution time: {agent.duration_ms} ms</span>
                    </div>
                  )}
                </div>
              </div>

              {/* View details button */}
              <div className="mt-4 pt-3 border-t border-[#EAE7F2] flex items-center justify-between">
                <span className="text-[10px] font-mono text-[#77748C]">{agent.agent_id}</span>
                <button
                  onClick={() => setSelectedAgentDetail(agent)}
                  className="px-3 py-1.5 rounded-xl bg-[#FAF9FE] hover:bg-[#F3F0FF] text-[#8B7CF6] font-semibold text-xs transition-colors flex items-center gap-1"
                >
                  <span>View Details</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Agent Detail Inspect Modal */}
      {selectedAgentDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl border border-[#EAE7F2] shadow-2xl max-w-xl w-full max-h-[85vh] overflow-y-auto">
            <div className="p-6 border-b border-[#EAE7F2] flex items-center justify-between sticky top-0 bg-white z-10">
              <div>
                <span className="text-[10px] uppercase font-bold text-[#77748C]">Agent Inspection Panel</span>
                <h3 className="font-bold text-base text-[#29263D]">{selectedAgentDetail.name}</h3>
              </div>
              <button
                onClick={() => setSelectedAgentDetail(null)}
                className="p-2 rounded-xl text-[#77748C] hover:bg-[#F3F0FF]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              <div className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2]">
                <strong className="block text-[#29263D] font-bold mb-1">Role & Responsibility</strong>
                <p className="text-[#77748C] leading-relaxed">{selectedAgentDetail.purpose}</p>
              </div>

              {selectedAgentDetail.last_input && (
                <div>
                  <strong className="block text-[#29263D] font-bold mb-1">Last Input Data</strong>
                  <pre className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] font-mono text-[11px] overflow-x-auto text-[#29263D]">
                    {JSON.stringify(selectedAgentDetail.last_input, null, 2)}
                  </pre>
                </div>
              )}

              {selectedAgentDetail.last_output && (
                <div>
                  <strong className="block text-[#29263D] font-bold mb-1">Last Output Summary</strong>
                  <pre className="p-3 rounded-2xl bg-[#FAF9FE] border border-[#EAE7F2] font-mono text-[11px] overflow-x-auto text-[#8B7CF6]">
                    {JSON.stringify(selectedAgentDetail.last_output, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-[#EAE7F2] bg-[#FAF9FE] rounded-b-3xl flex justify-end">
              <button
                onClick={() => setSelectedAgentDetail(null)}
                className="px-4 py-2 rounded-xl bg-[#8B7CF6] text-white font-semibold text-xs hover:bg-[#7A6AE6]"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
