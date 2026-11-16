import React from 'react';
import { X, BookOpen, Sparkles, Scale, Cpu, ShieldCheck } from 'lucide-react';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HelpModal: React.FC<HelpModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl border border-[#EAE7F2] shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto">
        <div className="p-6 border-b border-[#EAE7F2] flex items-center justify-between sticky top-0 bg-white z-10">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-[#F3F0FF] flex items-center justify-center text-[#8B7CF6]">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#29263D]">FairGig AI Documentation</h2>
              <p className="text-xs text-[#77748C]">UN Sustainable Development Goal 8: Decent Work & Economic Growth</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-[#77748C] hover:bg-[#F3F0FF] hover:text-[#29263D] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6 text-sm text-[#29263D]">
          {/* Section 1 */}
          <div>
            <h3 className="font-bold text-base text-[#8B7CF6] flex items-center gap-2">
              <Sparkles className="w-4 h-4" /> 1. Project Purpose & SDG 8 Alignment
            </h3>
            <p className="text-xs text-[#77748C] mt-2 leading-relaxed">
              FairGig AI solves the algorithmic unfairness problem prevalent in modern gig-work platforms.
              Instead of optimizing solely for travel proximity or raw platform profit—which often leads to
              worker burnout, opportunity starvation, and geographic discrimination—FairGig AI explicitly
              balances <strong>feasibility, worker suitability, ML success predictions, and workload equity</strong>.
            </p>
          </div>

          {/* Section 2 */}
          <div className="bg-[#FAF9FE] p-4 rounded-2xl border border-[#EAE7F2]">
            <h3 className="font-bold text-base text-[#29263D] flex items-center gap-2">
              <Scale className="w-4 h-4 text-[#8B7CF6]" /> 2. The WAFR Allocation Formula
            </h3>
            <p className="text-xs text-[#77748C] mt-1 mb-3">
              Task allocations are determined through the Workload-Aware Fair Ranking (WAFR) score:
            </p>
            <div className="bg-white p-3 rounded-xl border border-[#EAE7F2] font-mono text-xs text-[#8B7CF6] text-center font-bold">
              Score = 0.70 × P(success) + 0.30 × Efficiency + λ × Opportunity_Credit - λ × Workload_Pressure
            </div>
            <ul className="text-xs text-[#77748C] mt-3 space-y-1.5 list-disc list-inside">
              <li><strong>P(success):</strong> Predicted task completion likelihood from the dual ML ensemble.</li>
              <li><strong>Efficiency:</strong> Normalized operational efficiency based on travel distance and deadline pressure.</li>
              <li><strong>Opportunity Credit:</strong> Boosts workers with lower recent task exposure (1 - percentile exposure rank).</li>
              <li><strong>Workload Pressure:</strong> Calibrated penalty on excessive 7-day working hours to prevent burnout.</li>
              <li><strong>λ (Fairness Parameter):</strong> Configurable policy coefficient (default: 0.08).</li>
            </ul>
          </div>

          {/* Section 3 */}
          <div>
            <h3 className="font-bold text-base text-[#29263D] flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#8B7CF6]" /> 3. 6-Stage Multi-Agent Architecture
            </h3>
            <ol className="text-xs text-[#77748C] mt-2 space-y-2 list-decimal list-inside">
              <li><strong>Task Analysis Agent:</strong> Structures task parameters, validates constraints, and checks data quality.</li>
              <li><strong>Worker Suitability Agent:</strong> Enforces hard feasibility constraints (vehicle, skills, weight capacity, availability, travel deadline).</li>
              <li><strong>ML Success Prediction Service:</strong> Applies HistGradientBoosting (weight 0.5) and CatBoost (weight 0.5) over 27 features.</li>
              <li><strong>Fairness Evaluation Agent:</strong> Gathers exposure and workload signals, calculating opportunity credits and pressure terms.</li>
              <li><strong>Allocation Agent:</strong> Applies WAFR multi-objective scoring and ranks candidates.</li>
              <li><strong>Explainability Agent:</strong> Delivers clear, transparent, human-readable explanations with counterfactual comparisons.</li>
            </ol>
          </div>

          {/* Section 4 */}
          <div className="bg-[#D9F3E4]/30 p-4 rounded-2xl border border-emerald-200">
            <h3 className="font-bold text-sm text-emerald-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-700" /> Research Experiment Reference Metrics
            </h3>
            <p className="text-xs text-emerald-800 mt-1">
              Held-out task-grouped test evaluations recorded approximately:
              <strong> ROC-AUC: 0.9561</strong>, <strong>PR-AUC: 0.2431</strong> (against a 2.27% baseline prevalence),
              and <strong>Brier Score: 0.0187</strong>.
            </p>
          </div>
        </div>

        <div className="p-4 border-t border-[#EAE7F2] bg-[#FAF9FE] rounded-b-3xl flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-[#8B7CF6] hover:bg-[#7A6AE6] text-white font-medium text-xs shadow-xs transition-colors"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  );
};
